import nltk

nltk.download("vader_lexicon")
from nltk.sentiment import SentimentIntensityAnalyzer
import spacy
import re


class TextProcessor:

    def __init__(self):
        self._nltk = nltk
        self._nltk.download("punkt", quiet=True)
        self._nltk.download("averaged_perceptron_tagger", quiet=True)
        self._nltk.download("maxent_ne_chunker", quiet=True)
        self._nltk.download("words", quiet=True)
        self._nltk.download("stopwords", quiet=True)
        self._nltk.download("wordnet", quiet=True)
        self._nltk.download("vader_lexicon", quiet=True)
        self._nltk.download("omw", quiet=True)
        self._nltk.download("universal_tagset", quiet=True)
        self._nlp = spacy.load("en_core_web_sm")
        self._link_pattern = r"http\S+"
        self._markdown_link_pattern = r"\[([^\]]+)\]\((http\S+)\)"

    def clean_text(self, txt: str) -> str:
        txt = self.lowercase(txt)
        txt = self.replace_links(txt)
        txt = self.remove_punctuation(txt)
        return txt

    @staticmethod
    def get_sentiment_scores(sentence: str) -> (float, float, float, float):
        sia = SentimentIntensityAnalyzer()
        scores = sia.polarity_scores(sentence)
        return scores["compound"], scores["pos"], scores["neg"], scores["neu"]

    def replace_stopwords(self, txt: str) -> str:
        stop_words = set(self._nltk.corpus.stopwords.words("english"))
        return " ".join([word for word in txt.split() if word not in stop_words])

    @staticmethod
    def lowercase(txt: str) -> str:
        return txt.lower()

    @staticmethod
    def remove_punctuation(txt: str) -> str:
        return re.sub(r"[^\w\s\-\'\.,]", "", txt)

    def replace_links(self, txt: str) -> str:

        def replace_plain_links(match):
            if re.match(self._markdown_link_pattern, match.group(0)):
                return match.group(0)
            return "<link>"

        def replace_markdown_link(match):
            return match.group(1)

        txt = re.sub(self._markdown_link_pattern, replace_markdown_link, txt)
        txt = re.sub(
            r"(\[([^\]]+)\]\((http\S+)\))|" + self._link_pattern,
            replace_plain_links,
            txt,
        )
        return txt

    def lemmatize(self, tks: list[str]) -> list[str]:
        lemmatizer = self._nltk.stem.WordNetLemmatizer()
        return [lemmatizer.lemmatize(word) for word in tks]

    def pos_tag(self, tks: list[str]) -> list[tuple[str, str]]:
        return self._nltk.pos_tag(tks, tagset="universal")

    def get_sentiment(self, txt: str) -> (float, float, float, float):
        sia = self._nltk.sentiment.SentimentIntensityAnalyzer()
        return (
            sia.polarity_scores(txt)["compound"],
            sia.polarity_scores(txt)["pos"],
            sia.polarity_scores(txt)["neg"],
            sia.polarity_scores(txt)["neu"],
        )

    @property
    def nlp(self):
        return self._nlp
