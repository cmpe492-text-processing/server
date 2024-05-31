from nltk import sent_tokenize
import enum
from tagme import Annotation
import re

from nlp.text_processor import TextProcessor
from utils.tagme_manager import TagmeManager


class Platform(enum.Enum):
    REDDIT = "reddit"
    TWITTER = "twitter"

    def __str__(self):
        return self.value


class GenerateCorpus:
    def __init__(self, platform, platform_ext, platform_id, title, body):
        self.platform = platform
        self.platform_ext = platform_ext
        self.platform_id = platform_id
        self.title = title
        self.body = body
        self.text_processor = TextProcessor()
        self.tagme_manager = TagmeManager(rho=0.15)

    def adjust_entity_indices(self, original_text, entity):
        cleaned_begin = entity['begin']
        mention = entity['mention']

        original_index = original_text.find(mention, cleaned_begin - 5 if cleaned_begin > 5 else 0)
        if original_index != -1:
            entity['begin'] = original_index
            entity['end'] = original_index + len(mention)
        else:
            original_begin, original_end = self.find_closest_match(original_text, mention, cleaned_begin)
            if original_begin is not None and original_end is not None:
                entity['begin'] = original_begin
                entity['end'] = original_end
        return entity

    @staticmethod
    def find_closest_match(original_text, mention, start_index):
        pattern = re.escape(mention)
        for match in re.finditer(pattern, original_text, re.IGNORECASE):
            if abs(match.start() - start_index) <= len(mention):
                return match.start(), match.end()
        return None, None

    @staticmethod
    def find_full_sentence(doc, start_idx, end_idx):
        """
        This function finds the full sentence that contains the entity based on starting and ending index.
        """
        sentences = sent_tokenize(doc.text)
        for sentence in sentences:
            if doc.text.find(sentence) <= start_idx and doc.text.find(sentence) + len(sentence) >= end_idx:
                return sentence
        return ""

    def generate_corpus(self) -> dict:
        corpus: dict = {
            "platform": self.platform.value + "/" + self.platform_ext if self.platform_ext else self.platform.value,
            "id": self.platform_id,
            "title": self.title,
            "body": self.body,
            "version": 5}

        # clean text - remove special characters, remove stopwords, lower case, etc
        text_processor = TextProcessor()
        
        # Replace \ character with space to prevent tagme api error 
        cleaned_body = text_processor.clean_text(self.body)
        cleaned_title = text_processor.clean_text(self.title)

        
        
        # NER (Named Entity Recognition) - tag entities in text
        tagme_manager = TagmeManager(rho=0.15)
        if (cleaned_title == "" and cleaned_body == ""):
            return None
        

        # ENTITIES #
        if (cleaned_title != ""):
            tagged_title: list[Annotation] = tagme_manager.tag_text(cleaned_title)
        else:
            tagged_title = []
        if (cleaned_body != ""):
            tagged_body: list[Annotation] = tagme_manager.tag_text(cleaned_body)
        else:
            tagged_body = []

        # create entities with their base tagme information
        entities: list[dict] = []
        for annotation in tagged_title:
            entity = {
                "name": annotation.entity_title,
                "location": "title",
                "mention": annotation.mention,
                "begin": annotation.begin,
                "end": annotation.end,
                "confidence": annotation.score,
                "sentiment": None,
                "wiki_id": annotation.entity_id,
                "wiki_info": {},
            }

            info = tagme_manager.get_annotation_info(annotation)
            entity['wiki_info'] = info

            adjusted_entity = self.adjust_entity_indices(self.title, entity)
            entities.append(adjusted_entity)

        for annotation in tagged_body:
            entity = {
                "name": annotation.entity_title,
                "location": "body",
                "mention": annotation.mention,
                "begin": annotation.begin,
                "end": annotation.end,
                "confidence": annotation.score,
                "sentiment": None,
                "wiki_id": annotation.entity_id,
                "wiki_info": {},
            }
            info = tagme_manager.get_annotation_info(annotation)
            entity['wiki_info'] = info

            adjusted_entity = self.adjust_entity_indices(self.body, entity)
            entities.append(adjusted_entity)

        if len(entities) == 0:
            return corpus

        # filter entities that have their indices adjusted
        for entity in entities:
            if entity['location'] == 'title':
                found_word = self.title[entity['begin']:entity['end']]
            elif entity['location'] == 'body':
                found_word = self.body[entity['begin']:entity['end']]
            else:
                found_word = None
            if entity['mention'] != found_word:
                # concurrent modification exception?
                entities.remove(entity)

        # Process title and body with NLP
        title_doc = text_processor.nlp(self.title)
        body_doc = text_processor.nlp(self.body)

        for entity in entities:
            if entity['location'] == 'title':
                entity_doc = title_doc
            elif entity['location'] == 'body':
                entity_doc = body_doc
            else:
                continue  # Skip if location is not title or body

            # find the entity itself and its boundaries
            dependent_tokens = []
            for token in entity_doc:
                if entity['begin'] <= token.idx < entity['end']:
                    dependent_tokens.append(token)

            if not dependent_tokens:
                continue

            # Extend to full sentence for context
            min_index = min(token.idx for token in dependent_tokens)
            max_index = max(token.idx + len(token.text) for token in dependent_tokens)
            full_sentence = self.find_full_sentence(entity_doc, min_index, max_index)

            entity['sentence'] = full_sentence

            comp, pos, neg, neu = text_processor.get_sentiment_scores(full_sentence)
            entity['sentiment'] = {
                "compound": comp,
                "positive": pos,
                "negative": neg,
                "neutral": neu
            }

        corpus["entities"] = entities

        # ENTITY_GROUPS #

        entity_groups: list[object] = []
        for entity in entities:
            found = False
            for group in entity_groups:
                if group.get('sentence') == entity.get('sentence'):
                    group['entities'].append(entity['wiki_id'])
                    found = True
                    break
            if not found:
                entity_groups.append({
                    "sentence": entity.get('sentence', ''),
                    "entities": [entity['wiki_id']]
                })

        corpus["entity_groups"] = entity_groups
        return corpus
