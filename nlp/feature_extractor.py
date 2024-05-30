import json

from time import gmtime, strftime
import os

import requests
from dotenv import load_dotenv
from utils.database import DatabaseManager


class FeatureExtractor:

    def __init__(self, wiki_id):
        load_dotenv("../../.env")
        self.wiki_id = wiki_id
        self.db_dump_filepath = (
            os.getenv("PROJECT_X_ROOT") + "/resources/data/db_dumps/corpus.json"
        )

    @staticmethod
    def read_json_file(filepath):
        with open(filepath, "r") as file:
            data = json.load(file)
        return data

    @staticmethod
    def exporter(posts, center_entity_wiki_id, directory):
        direc = os.path.join(
            os.getenv("PROJECT_X_ROOT"), "resources/data/feature_extracted_data"
        )
        if not os.path.exists(direc):
            os.makedirs(
                direc
            )  # Creates the directory and all intermediate directories if they don't exist
        new_filename = f"{directory}_{center_entity_wiki_id}.json"
        with open(os.path.join(direc, new_filename), "w") as f:
            json.dump(posts, f, indent=2)
            print(f"Exported {len(posts)} {directory} to {new_filename}")

    @staticmethod
    def get_related_corpuses(center_entity_wiki_id, data):
        related_corpuses = []
        for post in data:
            entities = post.get("entities", [])
            for entity in entities:
                if "wiki_id" in entity and entity["wiki_id"] == center_entity_wiki_id:
                    related_corpuses.append(post)
                    break
        return related_corpuses

    @staticmethod
    def check_relatedness_from_db(db, entity_1, entity_2):
        small_entity = min(entity_1, entity_2)
        large_entity = max(entity_1, entity_2)
        return db.get_relatedness(small_entity, large_entity)

    @staticmethod
    def upsert_relatedness_to_db(db, entity_1, entity_2, relatedness):
        small_entity = min(entity_1, entity_2)
        large_entity = max(entity_1, entity_2)
        db.upsert_relatedness(small_entity, large_entity, relatedness)

    @staticmethod
    def add_relatedness(posts, center_entity_wiki_id, tagme_manager):
        db = DatabaseManager()
        for post in posts:
            entities = post.get("entities", [])
            for entity in entities:
                wiki_id = entity.get("wiki_id")
                if wiki_id:
                    relatedness = FeatureExtractor.check_relatedness_from_db(
                        db, center_entity_wiki_id, wiki_id
                    )
                    if relatedness:
                        entity["relatedness"] = relatedness
                    else:
                        relatedness_score = tagme_manager.relatedness_score(
                            center_entity_wiki_id, wiki_id
                        )
                        entity["relatedness"] = relatedness_score
                        FeatureExtractor.upsert_relatedness_to_db(
                            db, center_entity_wiki_id, wiki_id, relatedness_score
                        )
        return posts

    def get_most_occurred_entities(self, data, n):
        data = [entity for entity in data if entity["wiki_id"] != self.wiki_id]
        data.sort(key=lambda x: x["n"], reverse=True)
        return data[:n]

    def get_main_entity(self, data):
        # Find the entity that has the wiki id of the center entity
        for entity in data:
            if entity["wiki_id"] == self.wiki_id:
                return entity

    def create_extracted_features_json_wo_relatedness(self):
        raw_data = self.read_json_file(self.db_dump_filepath)
        print("read raw data", strftime("%Y-%m-%d %H:%M:%S", gmtime()))

        if not isinstance(raw_data, list):
            raise ValueError("Expected a list of dictionaries in JSON file.")

        related_corpuses_without_relatedness = self.get_related_corpuses(
            self.wiki_id, raw_data
        )
        print("got the corpuses", strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        # related_corpuses = self.add_relatedness(related_corpuses_without_relatedness, self.wiki_id, tagme_manager)
        # print('added the relatedness', strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        # data = related_corpuses
        data = related_corpuses_without_relatedness

        result = self.process_data(data)
        print("processed the data", strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        # self.exporter(result, self.wiki_id, "feature_extracted_data")
        most_occurred_x_entities = self.get_most_occurred_entities(result, 10)
        main_entity = self.get_main_entity(result)

        return result, most_occurred_x_entities, main_entity

    @staticmethod
    def process_data(data):
        results = {}
        for post in data:
            entities = post.get("entities", [])
            for entity in entities:
                wiki_id = entity["wiki_id"]
                if wiki_id in results.keys():
                    if (
                        entity.get("sentiment", None) is None
                        or results[wiki_id].get("sentiment", None) is None
                    ):
                        continue
                    old_neutral = results[wiki_id]["sentiment"].get("neutral", 0)
                    old_compound = results[wiki_id]["sentiment"].get("compound", 0)
                    old_positive = results[wiki_id]["sentiment"].get("positive", 0)
                    old_negative = results[wiki_id]["sentiment"].get("negative", 0)

                    new_neutral = entity["sentiment"].get("neutral", 0)
                    new_compound = entity["sentiment"].get("compound", 0)
                    new_positive = entity["sentiment"].get("positive", 0)
                    new_negative = entity["sentiment"].get("negative", 0)

                    results[wiki_id]["sentiment"] = {
                        "neutral": old_neutral + new_neutral,
                        "compound": old_compound + new_compound,
                        "positive": old_positive + new_positive,
                        "negative": old_negative + new_negative,
                    }

                    results[wiki_id]["n"] += 1

                    results[wiki_id]["sentiments_extended"].append(
                        entity.get("sentiment", {})
                    )
                else:
                    inserted_entity = {
                        "wiki_id": wiki_id,
                        "name": entity.get("name", ""),
                        "sentiment": entity.get("sentiment", {}),
                        "relatedness": entity.get("relatedness", None),
                        "sentiments_extended": [entity.get("sentiment", list())],
                        "n": 1,
                    }
                    results[wiki_id] = inserted_entity
        return list(results.values())


def main():
    feature_extractor = FeatureExtractor(4848272)
    feature_extractor.create_extracted_features_json_wo_relatedness()


if __name__ == "__main__":
    main()
