from tagme import Annotation, annotate
from nltk.sentiment import SentimentIntensityAnalyzer

from utils.tagme_manager import TagmeManager
from sqlalchemy import text


def get_basic_info(txt: str, ip, db) -> dict:
    """
    Extracts the entities in the given text. Does basic sentiment analysis for the whole text.

    :param txt:    Input String
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
    txt = txt.strip()
    entities: list[dict] = []
    annotations: list[Annotation] = annotate(txt).get_annotations(0.15)
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
    scores = sia.polarity_scores(txt)

    save_search(txt, ip, db)

    return {"text": txt, "entities": entities, "scores": scores}


def get_wikidata_info(curid) -> dict:
    tagme_manager = TagmeManager(rho=0.15)
    wiki_id = tagme_manager.get_annotation_info_with_id(curid)
    result = tagme_manager.get_wikidata_item_info_general(wiki_id)

    return {
        "description": result.get("description", ""),
        "item_info": result.get('item_info', {}),
        "instance_of": result.get('instance_of', [])
    }


def save_search(txt: str, ip, db):
    query = text("""
        INSERT INTO searches (text, ip) VALUES (:text, :ip);
    """)
    db.session.execute(query, {"text": txt, "ip": ip})
    db.session.commit()
    return
