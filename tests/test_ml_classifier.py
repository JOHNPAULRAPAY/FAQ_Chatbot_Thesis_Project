"""
Unit tests for the ML intent classifier.
"""
from app.ml.classifier import load_model, predict_intent


def test_model_loads_without_error():
    vectorizer, model = load_model()
    assert vectorizer is not None
    assert model is not None


def test_predict_returns_valid_confidence_range():
    vectorizer, model = load_model()
    tag, confidence = predict_intent("hello", vectorizer, model)
    assert 0.0 <= confidence <= 1.0


def test_predict_confident_on_exact_training_example():
    # A message identical to a training pattern should get high confidence
    vectorizer, model = load_model()
    tag, confidence = predict_intent("tuition", vectorizer, model)
    assert tag == "tuition_fees"
    assert confidence > 0.3  # loose threshold - tune based on your actual data