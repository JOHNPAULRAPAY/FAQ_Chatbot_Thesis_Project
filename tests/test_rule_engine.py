"""
Unit tests for the rule-based matching engine and text preprocessing.
"""
from app.chatbot.engine import rule_based_match, load_intents
from app.chatbot.preprocessing import normalize_text


def test_normalize_text_lowercases_and_strips_punctuation():
    assert normalize_text("Hello!!!") == "hello"
    assert normalize_text("  Tuition?  ") == "tuition"


def test_normalize_text_lemmatizes():
    # "documents" and "document" should normalize to the same lemma
    result_plural = normalize_text("documents")
    result_singular = normalize_text("document")
    assert result_plural == result_singular


def test_rule_match_finds_greeting():
    intents = load_intents()
    result = rule_based_match("hello there", intents)
    assert result == "greeting"


def test_rule_match_finds_tuition():
    intents = load_intents()
    result = rule_based_match("how much is the tuition", intents)
    assert result == "tuition_fees"


def test_rule_match_returns_none_for_gibberish():
    intents = load_intents()
    result = rule_based_match("asdkjhaskjd", intents)
    assert result is None