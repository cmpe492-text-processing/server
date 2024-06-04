import os
from dotenv import load_dotenv
import tagme
import requests
from tagme import Annotation


class TagmeManager:

    def __init__(self, rho):
        load_dotenv("../../.env")
        self.api_key = os.getenv("TAGME_API_KEY")
        tagme.GCUBE_TOKEN = self.api_key
        self.rho = rho

    def tag_posts(self, posts):
        post_all_annotations = []
        title_all_annotations = []

        for post in posts:
            post_annotations = self.process_text(post.cleaned_selftext)
            title_annotations = self.process_text(post.cleaned_title)
            post_all_annotations.append(post_annotations)
            title_all_annotations.append(title_annotations)

        return post_all_annotations, title_all_annotations

    @staticmethod
    def get_annotation_info(annotation):
        curid = annotation.entity_id
        params = {
            "action": "query",
            "prop": "pageprops",
            "pageids": curid,
            "format": "json",
        }
        wikipedia_api_url = "https://en.wikipedia.org/w/api.php"

        response = requests.get(wikipedia_api_url, params=params)
        data = response.json()
        try:
            wikidata_item_id = data["query"]["pages"][str(curid)]["pageprops"][
                "wikibase_item"
            ]
            return wikidata_item_id
        except KeyError as e:
            print(f"Error {e} fetching Wikidata URL from cur-id {curid}.")
            return None

    @staticmethod
    def get_annotation_info_with_id(curid):
        print(f"Fetching Wikidata URL for cur-id {curid}.")
        params = {
            "action": "query",
            "prop": "pageprops",
            "format": "json",
            "pageids": int(curid),
        }
        wikipedia_api_url = "https://en.wikipedia.org/w/api.php"

        response = requests.get(wikipedia_api_url, params=params)
        data = response.json()
        try:
            wikidata_item_id = data["query"]["pages"][str(curid)]["pageprops"][
                "wikibase_item"
            ]
            return wikidata_item_id
        except KeyError as e:
            print(f"Error {e} fetching Wikidata URL from cur-id {curid}.")
            return None

    @staticmethod
    def process_text(selftext):
        annotations = tagme.annotate(selftext)
        return annotations

    def tag_text(self, txt: str) -> list[Annotation]:
        try:
            return tagme.annotate(txt).get_annotations(self.rho)
        except Exception as e:
            print(f"Error tagging text, skipping")
            return []

    @staticmethod
    def get_wikidata_name(curid):
        attempts = 0
        max_attempts = 5
        wikidata_entity_url = (
            f"https://www.wikidata.org/wiki/Special:EntityData/{curid}.json"
        )

        while attempts < max_attempts:
            response = requests.get(wikidata_entity_url)
            if response.status_code == 200:
                data = response.json()
                return data["entities"][curid]["labels"]["en"]["value"]
            else:
                attempts += 1

        return None

    @staticmethod
    def relatedness_score(wid1, wid2):
        try:
            relations = tagme.relatedness_wid((wid1, wid2))
            for relation in relations.relatedness:
                return relation.rel
        except Exception as e:
            print(f"Error fetching relatedness score: {e}")
            return None

    def get_relatedness_map(self,
                            entities: list[(int, int)],
                            cache,
                            debug=False) -> dict[(int, int), float]:

        relatedness_map: dict[(int, int), float] = {}
        entities = [tuple(sorted(entity_pair)) for entity_pair in entities]
        tagme.GCUBE_TOKEN = self.api_key
        total_entities = len(entities)

        if debug:
            print(f"Total entities to fetch relatedness scores: {total_entities}")

        entities_to_fetch = []
        cache_hits = 0
        cache_misses = 0

        for entity_pair in entities:
            cache_key = f"{entity_pair[0]}_{entity_pair[1]}"
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                relatedness_map[entity_pair] = cached_value
                cache_hits += 1
            else:
                entities_to_fetch.append(entity_pair)
                cache_misses += 1

        if debug:
            print(f"Cache hits: {cache_hits}, Cache misses: {cache_misses}")
            print(f"Fetching relatedness scores for {len(entities_to_fetch)} entity pairs.")

        if entities_to_fetch:
            for j in range(5):
                try:
                    relations = tagme.relatedness_wid(entities_to_fetch)
                    for relation in relations.relatedness:
                        entity_pair = (int(relation.title1), int(relation.title2))
                        r_val = float(relation.rel)
                        relatedness_map[entity_pair] = r_val
                        cache_key = f"{entity_pair[0]}_{entity_pair[1]}"
                        cache.set(cache_key, r_val)
                    break
                except Exception as e:
                    print(f"Error fetching relatedness score: {e}")

        return relatedness_map

    @staticmethod
    def fetch_label_from_wikidata(q_id):
        """Fetches the label for a given Q value from Wikidata."""
        url = f"https://www.wikidata.org/wiki/Special:EntityData/{q_id}.json"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return data["entities"][q_id]["labels"]["en"]["value"]
        except requests.RequestException as e:
            print(f"Failed to fetch data from Wikidata: {e}")
            return None

    @staticmethod
    def get_wikidata_item_info_general(wikidata_item_id):
        print(f"Fetching Wikidata API data for {wikidata_item_id}.")
        attempts = 0
        max_attempts = 5
        wikidata_entity_url = (
            f"https://www.wikidata.org/wiki/Special:EntityData/{wikidata_item_id}.json"
        )

        while attempts < max_attempts:
            response = requests.get(wikidata_entity_url)
            if response.status_code == 200:
                data = response.json()
                description = (
                    data.get("entities", {})
                    .get(wikidata_item_id, {})
                    .get("descriptions", {})
                    .get("en", {})
                    .get("value", "")
                ).capitalize()

                item_info = {
                    "instance of": data.get("entities", {})
                    .get(wikidata_item_id, {})
                    .get("claims", {})
                    .get("P31", []),
                    "sex or gender": data.get("entities", {})
                    .get(wikidata_item_id, {})
                    .get("claims", {})
                    .get("P21", []),
                    "country": data.get("entities", {})
                    .get(wikidata_item_id, {})
                    .get("claims", {})
                    .get("P17", []),
                    "occupation": data.get("entities", {})
                    .get(wikidata_item_id, {})
                    .get("claims", {})
                    .get("P106", []),
                    "given name": data.get("entities", {})
                    .get(wikidata_item_id, {})
                    .get("claims", {})
                    .get("P735", []),
                    "date of birth": data.get("entities", {})
                    .get(wikidata_item_id, {})
                    .get("claims", {})
                    .get("P569", []),
                    "date of death": data.get("entities", {})
                    .get(wikidata_item_id, {})
                    .get("claims", {})
                    .get("P570", []),
                    "place of birth": data.get("entities", {})
                    .get(wikidata_item_id, {})
                    .get("claims", {})
                    .get("P19", []),
                    "place of death": data.get("entities", {})
                    .get(wikidata_item_id, {})
                    .get("claims", {})
                    .get("P20", []),
                    "country of citizenship": data.get("entities", {})
                    .get(wikidata_item_id, {})
                    .get("claims", {})
                    .get("P27", []),
                    "educated at": data.get("entities", {})
                    .get(wikidata_item_id, {})
                    .get("claims", {})
                    .get("P69", []),
                    "employer": data.get("entities", {})
                    .get(wikidata_item_id, {})
                    .get("claims", {})
                    .get("P108", []),
                    "award received": data.get("entities", {})
                    .get(wikidata_item_id, {})
                    .get("claims", {})
                    .get("P166", []),
                    "position held": data.get("entities", {})
                    .get(wikidata_item_id, {})
                    .get("claims", {})
                    .get("P39", []),
                    "work location": data.get("entities", {})
                    .get(wikidata_item_id, {})
                    .get("claims", {})
                    .get("P937", []),
                    "field of work": data.get("entities", {})
                    .get(wikidata_item_id, {})
                    .get("claims", {})
                    .get("P101", []),
                }

                item_info = {k: v for k, v in item_info.items() if v is not None}
                item_info_instance_of_array = []
                for values in item_info.get("instance of", []):
                    result = TagmeManager.fetch_label_from_wikidata(
                        values["mainsnak"]["datavalue"]["value"]["id"]
                    )
                    if result:
                        item_info_instance_of_array.append(result)

                return {
                    "item_info": item_info,
                    "description": description,
                    "instance_of": item_info_instance_of_array,
                }
            else:
                attempts += 1
                print(
                    f"Attempt {attempts}/{max_attempts} failed with status code {response.status_code}. Retrying..."
                )

        print("Error fetching Wikidata API data after maximum attempts.")
        return {}
