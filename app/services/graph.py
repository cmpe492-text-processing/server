from utils.tagme_manager import TagmeManager
from sqlalchemy import text
from collections import defaultdict
from itertools import combinations
import numpy as np
from numba import jit


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


def get_graph(wiki_id: int, db):
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
    relatedness_map = tagme_mng.get_relatedness_map(key_list)

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
                "sentiment": sentiment_score
            })
            okay.add(entity_wiki_id)

    links = [
        {
            "source": key[0],
            "target": key[1],
            "thickness": int(occurrences[key]),
            "weight": float(relatedness[key])
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
