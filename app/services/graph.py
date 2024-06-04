from dataclasses import dataclass

from utils.tagme_manager import TagmeManager
from sqlalchemy import text
from collections import defaultdict
from itertools import combinations
from numba import jit
from scipy.sparse import lil_matrix
import numpy as np
import time
import networkx as nx



@dataclass
class Sentiment:
    positive: float
    negative: float
    neutral: float
    compound: float


@dataclass
class Entity:
    id: int
    name: str
    sentiment: Sentiment
    count: int = 1


@jit(nopython=True)
def compute_occurrences(temp_occurrences):
    n = len(temp_occurrences)
    occ = {}
    for i in range(n):
        for j in range(i + 1, n):
            key = (temp_occurrences[i], temp_occurrences[j])
            if key in occ:
                occ[key] += 1
            else:
                occ[key] = 1
    return occ


def sigmoid_mapping_co_occ(co_occ_rr, co_occ_min, co_occ_max):
    # Normalize co_occ_rr to the range [0, 1]
    normalized_rr = (co_occ_rr - co_occ_min) / (co_occ_max - co_occ_min)

    # Apply a sigmoid-like transformation
    mapped_value = 1 / (1 + np.exp(-10 * (normalized_rr - 0.5)))

    # Scale to the range [0.1, 1]
    scaled_value = 0.1 + 0.9 * mapped_value

    # [1, 10]
    return 10 * scaled_value

def mapping_n_size(n_size, min_n_size, max_n_size):
    # Normalize n_size to the range [0, 1]
    normalized_n_size = (n_size - min_n_size) / (max_n_size - min_n_size)

    # apply a linear transformation that is more sensitive to the lower values
    mapped_value = np.sqrt(normalized_n_size)

    # Scale to the range [3, 10]
    scaled_value = 3 + 7 * mapped_value

    return  scaled_value


def get_graph_v2(wiki_id: int, db, cache, entity_count_threshold=500, mean_multiplier=1.0):
    corpuses = fetch_corpuses_by_entity_id(wiki_id, db)

    entityid_to_index = {}
    index_to_entity = []

    # Assign indices to entities and store all entity fields
    for corp in corpuses:
        for entity in corp.get("entities", []):
            entity_id = entity["wiki_id"]
            sentiment = entity["sentiment"]
            if sentiment is None:
                sentiment = {"positive": 0, "negative": 0, "neutral": 0, "compound": 0}
            if entity_id not in entityid_to_index:
                entityid_to_index[entity_id] = len(index_to_entity)
                index_to_entity.append(
                    Entity(
                        id=entity_id,
                        name=entity["name"],
                        sentiment=Sentiment(
                            positive=sentiment["positive"],
                            negative=sentiment["negative"],
                            neutral=sentiment["neutral"],
                            compound=sentiment["compound"]
                        )
                    )
                )
            else:
                index = entityid_to_index[entity_id]
                index_to_entity[index].count += 1
                index_to_entity[index].sentiment = Sentiment(
                    positive=index_to_entity[index].sentiment.positive + sentiment["positive"],
                    negative=index_to_entity[index].sentiment.negative + sentiment["negative"],
                    neutral=index_to_entity[index].sentiment.neutral + sentiment["neutral"],
                    compound=index_to_entity[index].sentiment.compound + sentiment["compound"]
                )

    n = len(index_to_entity)
    co_occ = lil_matrix((n, n), dtype=np.int32)

    # Fill the co-occurrence matrix
    for corp in corpuses:
        entity_ids = [entityid_to_index[entity.get("wiki_id")] for entity in corp.get("entities", [])]
        for i, j in combinations(entity_ids, 2):
            co_occ[i, j] += 1
            co_occ[j, i] += 1

    # Sum the co-occurrence counts for each entity
    co_occ_sums = np.array(co_occ.sum(axis=1)).flatten()

    # Use argpartition to find the top co-occurrence entities
    if len(co_occ_sums) <= entity_count_threshold:
        filtered_indices = np.arange(len(co_occ_sums))
    else:
        filtered_indices = np.argpartition(co_occ_sums, -entity_count_threshold)[-entity_count_threshold:]
        filtered_indices = filtered_indices[np.argsort(-co_occ_sums[filtered_indices])]

    nodes = [index_to_entity[i] for i in filtered_indices]

    for corp in corpuses:
        entity_groups = corp.get("entity_groups", [])
        for group in entity_groups:
            group_entities = [entityid_to_index[entity_id] for entity_id in group.get("entities", [])]
            group_entities = [i for i in group_entities if i in filtered_indices]
            for i, j in combinations(group_entities, 2):
                co_occ[i, j] += 1
                co_occ[j, i] += 1

    links = []
    # get the median of non-zero co-occurrences
    non_zero = np.hstack(co_occ.data)
    co_occ_mean = np.average(non_zero)
    co_occ_max = np.sqrt(np.max(non_zero))
    co_occ_min = np.sqrt(np.min(non_zero))

    keys = [(index_to_entity[i].id, index_to_entity[j].id) for i, j in combinations(filtered_indices, 2)
            if co_occ[i, j] > (mean_multiplier * co_occ_mean)]
    relatedness = TagmeManager(0.1).get_relatedness_map(keys, cache, debug=True)

    for key in keys:
        source, target = key
        co_occ_rr = np.sqrt(co_occ[
                                entityid_to_index[source],
                                entityid_to_index[target]
                            ])
        links.append({
            "source": source,
            "target": target,
            "thickness": int(
                sigmoid_mapping_co_occ(co_occ_rr, co_occ_min, co_occ_max)
            ),
            "weight": float(relatedness.get(
                (source, target), 0)
            )
        })

    G = nx.Graph()

    for node in nodes:
        G.add_node(node.id, name=node.name, sentiment=node.sentiment.compound / node.count)

    for link in links:
        # if link["weight"] > 0 or link["thickness"] > 1.1:
        G.add_edge(link["source"], link["target"], thickness=link["thickness"], weight=link["weight"])

    main_component = None
    for component in nx.connected_components(G):
        if wiki_id in component:
            main_component = component
            break

    if main_component is not None:
        G = G.subgraph(main_component).copy()

    for node in G.nodes:
        if G.nodes[node]['sentiment'] == 0:
            neighbors = list(G.neighbors(node))
            if neighbors:
                weighted_sum = 0
                total_weight = 0
                for neighbor in neighbors:
                    sentiment = G.nodes[neighbor]['sentiment']
                    if sentiment != 0:
                        weight = G[node][neighbor]['weight']
                        weighted_sum += sentiment * weight
                        total_weight += weight
                if total_weight > 0:
                    G.nodes[node]['sentiment'] = weighted_sum / total_weight

    min_neighbours = 1
    max_neighbours = 0
    for node in G.nodes:
        max_neighbours = max(max_neighbours, len(list(G.neighbors(node))))

    return {
        "nodes": [
            {
                "id": node,
                "name": G.nodes[node]["name"],
                "sentiment": round(G.nodes[node]["sentiment"], 3),
                "size":
                    mapping_n_size(
                        len(list(G.neighbors(node))),
                        min_neighbours,
                        max_neighbours
                    )
            }
            for node in G.nodes
        ],
        "links": [
            {
                "source": u,
                "target": v,
                "thickness": round(G[u][v]["thickness"], 3),
                "weight": round(G[u][v]["weight"], 3)
            }
            for u, v in G.edges
        ]
    }


def get_graph(wiki_id: int, db, cache):
    """
    Get the graph for the given entity.

    :param db:          Database
    :param wiki_id:     Wikidata ID
    :return:            {
                            nodes: [
                                {
                                    id: int,
                                    name: str,
                                    type: str
                                }
                            ],
                            links: [
                                {
                                    source: int,
                                    target: int,
                                    type: str
                                }
                            ]
                        }
    """

    corpuses = fetch_corpuses_by_entity_id(wiki_id, db)

    occurrences = defaultdict(int)
    sentiment = defaultdict(list)
    entity_titles = {}

    for corp in corpuses:
        entities = corp.get("entities", [])
        temp_occurrences = []

        for entity in entities:
            entity_wiki_id = entity.get("wiki_id")
            if entity_wiki_id:
                temp_occurrences.append(entity_wiki_id)
                sentiment_scores = entity.get("sentiment")
                if sentiment_scores:
                    sentiment[entity_wiki_id].append(sentiment_scores)

                entity_title = entity.get("name")
                if entity_title:
                    entity_titles[entity_wiki_id] = entity_title

        temp_occurrences = np.array(temp_occurrences, dtype=np.int32)
        temp_occurrences.sort()
        occ = compute_occurrences(temp_occurrences)
        for key, value in occ.items():
            occurrences[key] += value

        entity_groups = corp.get("entity_groups", [])
        for group in entity_groups:
            group_entities = [e for e in group.get("entities", [])]
            group_entities = np.array(group_entities, dtype=np.int32)
            group_entities.sort()
            occ = compute_occurrences(group_entities)
            for key, value in occ.items():
                occurrences[key] += value

    key_list = list(occurrences.keys())
    tagme_mng = TagmeManager(0.1)
    relatedness_map = tagme_mng.get_relatedness_map(key_list, cache)

    relatedness = {key: relatedness_map[(str(key[0]), str(key[1]))] for key in key_list}

    nodes = []
    okay = set()
    for entity_wiki_id, entity_title in entity_titles.items():
        sentiment_scores = sentiment.get(entity_wiki_id, [])
        if sentiment_scores:
            sentiment_score = float(np.mean([score.get("compound", 0) for score in sentiment_scores]))
            nodes.append({
                "id": int(entity_wiki_id),
                "name": entity_title,
                "sentiment": round(sentiment_score, 3)
            })
            okay.add(entity_wiki_id)

    links = [
        {
            "source": key[0],
            "target": key[1],
            "thickness": round(float(occurrences[key]), 3),
            "weight": round(float(relatedness[key]), 3)
        }
        for key in occurrences
        if key[0] in okay and key[1] in okay
    ]

    return {
        "nodes": nodes,
        "links": links
    }


def fetch_corpuses_by_entity_id(entity_id: int, db):
    query = text("""
    SELECT data
    FROM corpuses
    WHERE EXISTS (
        SELECT 1
        FROM jsonb_array_elements(data->'entities') as entity
        WHERE entity->>'wiki_id' = CAST(:entity_id AS TEXT)
    );
    """)
    result = db.session.execute(query, {'entity_id': entity_id})
    rows = result.fetchall()
    return [row[0] for row in rows]
