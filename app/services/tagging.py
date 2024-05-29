from tagme import Annotation, annotate
from nltk.sentiment import SentimentIntensityAnalyzer

from utils.tagme_manager import TagmeManager


def get_basic_info(text: str) -> dict:
    """
    Extracts the entities in the given text. Does basic sentiment analysis for the whole text.

    :param text:    Input String
    :return:        {
                        text: str,
                        entities: {
                                    name: str,
                                    mention: str,
                                    begin: int,
                                    end: int,
                                    confidence: float,
                                    wiki_id: float,
                                    wiki_info: dict
                                    },
                        scores: {
                            compound: float,
                            neu: float,
                            pos: float,
                            neg: float
                            }
                    }
    """
    text = text.strip()
    entities: list[dict] = []
    annotations: list[Annotation] = annotate(text).get_annotations(0.15)
    for annotation in annotations:
        entity = {
            "name": annotation.entity_title,
            "mention": annotation.mention,
            "begin": annotation.begin,
            "end": annotation.end,
            "confidence": annotation.score,
            "wiki_id": annotation.entity_id,
        }
        entities.append(entity)

    sia = SentimentIntensityAnalyzer()
    scores = sia.polarity_scores(text)

    return {"text": text, "entities": entities, "scores": scores}


def get_wikidata_info(curid) -> dict:

    tagme_manager = TagmeManager(rho=0.15)
    wiki_id = tagme_manager.get_annotation_info_with_id(curid)
    result = tagme_manager.get_wikidata_item_info_general(wiki_id)

    return {
        "description": result.get("description", ""),
        "item_info": result.get('item_info', {}),
        "instance_of": result.get('instance_of', [])
    }
