import math
from time import gmtime, strftime
from sqlalchemy import text
from dotenv import load_dotenv


class OTFFeatureExtractor:

    def __init__(self, wiki_id, db):
        load_dotenv(".env")
        self.wiki_id = wiki_id
        self.db = db

    
    # Instead of reading from a json file, I will replace it with a SQL query
    def fetch_corpuses_with_entity_id(self):
        query = text("""
        SELECT data
        FROM corpuses
        WHERE EXISTS (
            SELECT 1
            FROM jsonb_array_elements(data->'entities') as entity
            WHERE entity->>'wiki_id' = CAST(:entity_id AS TEXT)
        );
        """)
        result = self.db.session.execute(query, {'entity_id': self.wiki_id})
        rows = result.fetchall()
        return [row[0] for row in rows]
    
    def fetch_main_entity_with_id(self, data):
        for entity in data:
            if entity["wiki_id"] == self.wiki_id:
                return entity

    def prepare_result(self):
        print("got the request", strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        raw_data = self.fetch_corpuses_with_entity_id()
        print("read raw data", strftime("%Y-%m-%d %H:%M:%S", gmtime()))

        if not isinstance(raw_data, list):
            raise ValueError("Expected a list of dictionaries in JSON file.")

        result = self.process_data(raw_data)
        print("processed the data", strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        main_entity = self.fetch_main_entity_with_id(result)
        occurred_entities = sorted(result, key=lambda x: x["n"], reverse=True)

        return result, occurred_entities ,main_entity

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
    otf_feature_extractor = OTFFeatureExtractor(4848272)
    print(otf_feature_extractor.fetch_corpuses_with_entity_id())

if __name__ == "__main__":
    main()
