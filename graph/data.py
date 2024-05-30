import json
import os

from dotenv import load_dotenv

from utils.database import DatabaseManager
from utils.tagme_manager import TagmeManager

DEBUG = True

load_dotenv(".env")

raw_path = os.path.join("resources", "data", "db_dumps", "corpus.json")
raw_data: list[dict] = []

# (entity1, entity2) -> occurrences
# entity1, entity2 are wiki_ids, sorted in ascending order
occurrences: dict[(int, int), int] = {}

# (entity1, entity2) -> relatedness score
relatedness: dict[(int, int), float] = {}

# wiki_id -> list of sentiment scores
sentiment: dict[int, list[dict]] = {}

# wiki_id -> entity_title
entity_titles: dict[int, str] = {}


def load_data():
    global raw_data, raw_path
    with open(raw_path, "r") as f:
        raw_data = json.load(f)


def process_data():
    global raw_data, occurrences, relatedness, sentiment, entity_titles
    for post in raw_data:
        entities = post.get("entities", [])
        temp_occurrences = []
        for entity in entities:
            wiki_id = entity.get("wiki_id")
            if wiki_id:
                temp_occurrences.append(wiki_id)
                sentiment_scores = entity.get("sentiment")
                if sentiment_scores:
                    if wiki_id not in sentiment:
                        sentiment[wiki_id] = []
                    sentiment[wiki_id].append(sentiment_scores)

                entity_title = entity.get("name")
                if entity_title:
                    entity_titles[wiki_id] = entity_title

        temp_occurrences.sort()
        for i in range(len(temp_occurrences)):
            for j in range(i + 1, len(temp_occurrences)):
                key = (temp_occurrences[i], temp_occurrences[j])
                occurrences[key] = occurrences.get(key, 0) + 1

        entity_groups = post.get("entity_groups", [])
        for group in entity_groups:
            group_entities = group.get("entities", [])
            group_entities.sort()
            for i in range(len(group_entities)):
                for j in range(i + 1, len(group_entities)):
                    key = (group_entities[i], group_entities[j])
                    occurrences[key] = occurrences.get(key, 0) + 1

    if DEBUG:
        print(f"Processed {len(raw_data)} posts")
        print(f"Found {len(occurrences)} edges")
        print(f"Found {len(sentiment)} entities with sentiment scores")
        print(f"Found {len(entity_titles)} entity titles")

    # key list
    key_list = list(occurrences.keys())
    tagme_mng = TagmeManager(0.1)
    relatedness_map = tagme_mng.get_relatedness_map(key_list, DEBUG)

    relatedness = {key: relatedness_map[(str(key[0]), str(key[1]))] for key in key_list}


def get_relatedness(entity1, entity2):
    db = DatabaseManager()
    db.create_connection()

    rlt = db.get_relatedness(entity1, entity2)
    if rlt:
        return rlt

    tagme_manager = TagmeManager(0.1)
    rlt = tagme_manager.relatedness_score(entity1, entity2)
    db.upsert_relatedness(entity1, entity2, rlt)
    db.close_connection(False)
    return rlt


def export_graph(prefix="general"):
    global raw_data, occurrences, relatedness, sentiment, entity_titles


def main_export_general():
    print("\033[1mStarting...\033[0m")
    load_data()

    print("\033[1mProcessing data...\033[0m")
    process_data()

    print("\033[1mExporting graph...\033[0m")
    export_graph()

    print("\033[1mDone!\033[0m")


def main_export_entity(entity_id):
    global raw_data
    print("\033[1mStarting...\033[0m")
    load_data()

    # filter raw data to posts that contain the entity
    raw_data = [
        post
        for post in raw_data
        if entity_id in [entity["wiki_id"] for entity in post.get("entities", [])]
    ]

    print("\033[1mProcessing data...\033[0m")
    process_data()

    print("\033[1mExporting graph...\033[0m")
    export_graph(str(entity_id))

    print("\033[1mDone!\033[0m")


def export(
    entity_id: int = None,
    node_limit: int = None,
    edge_limit: int = None,
    relatedness_threshold: float = None,
    sentiment_threshold: float = None,
):
    global raw_data, occurrences, relatedness, sentiment, entity_titles
    print("\033[1mStarting...\033[0m")
    load_data()

    if entity_id:
        raw_data = [
            post
            for post in raw_data
            if entity_id in [entity["wiki_id"] for entity in post.get("entities", [])]
        ]

    print("\033[1mProcessing data...\033[0m")
    process_data()

    if sentiment_threshold:
        sentiment = {
            k: v
            for k, v in sentiment.items()
            if any(
                [abs(score.get("compound", 0)) >= sentiment_threshold for score in v]
            )
        }
        entity_titles = {k: v for k, v in entity_titles.items() if k in sentiment}

    if relatedness_threshold:
        relatedness = {
            k: v for k, v in relatedness.items() if v >= relatedness_threshold
        }
        occurrences = {k: v for k, v in occurrences.items() if k in relatedness}

    if node_limit:
        sentiment = {
            k: v
            for k, v in sorted(
                sentiment.items(),
                key=lambda x: sum([score.get("compound", 0) for score in x[1]]),
                reverse=True,
            )[:node_limit]
        }
        entity_titles = {k: v for k, v in entity_titles.items() if k in sentiment}

    if edge_limit:
        occurrences = {
            k: v
            for k, v in sorted(occurrences.items(), key=lambda x: x[1], reverse=True)[
                :edge_limit
            ]
        }
        relatedness = {k: v for k, v in relatedness.items() if k in occurrences}

    print("\033[1mExporting graph...\033[0m")
    export_graph(prefix=str(entity_id) if entity_id else "general")


"""
        edges.csv
        entity1,entity2,edge_thickness,edge_weight
        id, id, int (occurrences), float (relatedness score)
        
        nodes.csv
        wiki_id,entity_title,sentiment
        id, str, float (aggregate sentiment score)
"""

if __name__ == "__main__":
    export(entity_id=4848272)  # , node_limit=300, edge_limit = 10000)
