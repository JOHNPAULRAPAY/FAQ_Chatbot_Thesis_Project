"""
ML intent classifier: trains a simple text classification model on the
patterns in intents.json, and predicts intent + confidence for new text.

Approach: TF-IDF (turns text into numeric features based on word
importance) + Logistic Regression (a simple, fast, interpretable
classifier -- a solid baseline before trying anything fancier).
"""
import json
import os
import pickle

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from app.chatbot.preprocessing import normalize_text

INTENTS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "intents.json"
)
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")


def load_training_data(path: str = INTENTS_PATH):
    """
    Reads intents.json and flattens it into two parallel lists:
    texts = ["hi", "hello", ...]
    labels = ["greeting", "greeting", ...]
    (The 'fallback' intent is skipped since it has no patterns to train on.)
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts = []
    labels = []

    for intent in data["intents"]:
        if not intent["patterns"]:
            continue
        for pattern in intent["patterns"]:
            texts.append(normalize_text(pattern))
            labels.append(intent["tag"])

    return texts, labels


def train_model():
    """
    Trains the TF-IDF + Logistic Regression pipeline and saves it to disk.
    Run this whenever intents.json changes (new intents/patterns added).
    """
    texts, labels = load_training_data()

    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(texts)

    model = LogisticRegression()
    model.fit(X, labels)

    with open(MODEL_PATH, "wb") as f:
        pickle.dump((vectorizer, model), f)

    print(f"Model trained on {len(texts)} examples across {len(set(labels))} intents.")
    print(f"Saved to {MODEL_PATH}")


def load_model():
    """Loads the trained vectorizer + model from disk."""
    with open(MODEL_PATH, "rb") as f:
        vectorizer, model = pickle.load(f)
    return vectorizer, model


def predict_intent(text: str, vectorizer, model):
    """
    Predicts the intent for a piece of text.
    Returns (predicted_tag, confidence) where confidence is 0.0-1.0.
    """
    clean_text = normalize_text(text)
    X = vectorizer.transform([clean_text])

    predicted_tag = model.predict(X)[0]
    probabilities = model.predict_proba(X)[0]
    confidence = max(probabilities)

    return predicted_tag, confidence


if __name__ == "__main__":
    train_model()