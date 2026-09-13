"""
Text normalization utilities, now using spaCy for lemmatization.
Lemmatization reduces words to their base form (e.g. "enrolling" -> "enroll"),
so pattern matching and ML training are less sensitive to word variations.
"""
import string
import spacy

# Load once at import time - loading this model is relatively slow,
# so we don't want to do it on every function call.
_nlp = spacy.load("en_core_web_sm")


def normalize_text(text: str) -> str:
    """
    Cleans and lemmatizes user input:
    - Lowercases, strips whitespace
    - Removes punctuation
    - Lemmatizes each word (e.g. "enrolled" -> "enroll", "documents" -> "document")
    - Collapses multiple spaces into one
    """
    text = text.lower().strip()
    text = text.translate(str.maketrans("", "", string.punctuation))

    doc = _nlp(text)
    lemmatized_words = [token.lemma_ for token in doc if token.lemma_.strip()]

    return " ".join(lemmatized_words)