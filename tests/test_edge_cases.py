"""
Tests for unknown/ambiguous input and fallback/clarification behavior.
"""
from app.chatbot.engine import load_intents, get_response
from app.chatbot.conversation import ConversationState


def test_gibberish_triggers_fallback():
    intents = load_intents()
    response = get_response("xkjhaskjdh", intents)
    assert "didn't quite understand" in response


def test_repeated_fallback_triggers_escalation():
    intents = load_intents()
    state = ConversationState()

    # Trigger 3 fallbacks in a row
    get_response("asdkjh", intents, state)
    get_response("qweiop", intents, state)
    response = get_response("zxcvbn", intents, state)

    assert "having trouble understanding" in response


def test_goodbye_always_exits_regardless_of_ml():
    # 'bye' must ALWAYS exit - this is a RULE_ONLY_INTENT, critical to verify
    intents = load_intents()
    response = get_response("bye", intents)
    assert response == "__EXIT__"


def test_empty_string_does_not_crash():
    intents = load_intents()
    # Should not raise an exception, even on empty input
    response = get_response("", intents)
    assert isinstance(response, str)