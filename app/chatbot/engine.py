"""
Hybrid chatbot engine: combines rule-based matching (for critical intents
and as a fallback) with ML-based intent classification (for general
recognition). Confidence thresholds decide which result to trust.
"""
import json
import os
import random

from app.chatbot.llm_layer import ask_llm
from app.chatbot.entities import extract_program
from app.chatbot.preprocessing import normalize_text
from app.ml.classifier import load_model, predict_intent

PROGRAM_AWARE_INTENTS = {"tuition_fees", "admission_requirements", "enrollment_process"}

INTENTS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "intents.json"
)

CONFIDENCE_THRESHOLD = 0.5  # below this, don't trust the ML prediction

# Intents that MUST be handled by rules, never by ML, because getting
# them wrong has outsized consequences (e.g. accidentally ending a chat).
RULE_ONLY_INTENTS = {"goodbye"}


def load_intents(path: str = INTENTS_PATH) -> list:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["intents"]


def get_responses_by_tag(tag: str, intents: list) -> list:
    for intent in intents:
        if intent["tag"] == tag:
            return intent["responses"]
    return ["Sorry, I didn't quite understand that. Could you rephrase your question?"]


def rule_based_match(user_input: str, intents: list) -> str | None:
    """
    Word-level rule matching (from Step 5). Returns a matching intent tag,
    or None if nothing matches confidently.
    """
    clean_text = normalize_text(user_input)
    input_words = set(clean_text.split())

    for intent in intents:
        for pattern in intent["patterns"]:
            pattern_words = set(normalize_text(pattern).split())
            if not pattern_words:
                continue
            if pattern_words.issubset(input_words):
                return intent["tag"]

    return None


# Load the ML model once, at import time (not per-request, for performance)
try:
    _vectorizer, _model = load_model()
except FileNotFoundError:
    _vectorizer, _model = None, None


def find_intent_tag(user_input: str, intents: list) -> str:
    """
    Decides the final intent tag using the hybrid strategy:
    1. Rule match on a RULE_ONLY_INTENTS -> always wins immediately.
    2. Otherwise, try ML prediction. If confident enough, use it.
    3. If ML isn't confident, fall back to rule matching.
    4. If neither works, return 'fallback'.
    """
    rule_tag = rule_based_match(user_input, intents)

    # Step 1: critical intents always go through rules first
    if rule_tag in RULE_ONLY_INTENTS:
        return rule_tag

    # Step 2: try ML
    if _model is not None:
        ml_tag, confidence = predict_intent(user_input, _vectorizer, _model)
        if confidence >= CONFIDENCE_THRESHOLD and ml_tag not in RULE_ONLY_INTENTS:
            return ml_tag

    # Step 3: fall back to rules if ML wasn't confident
    if rule_tag is not None:
        return rule_tag

    # Step 4: nothing worked
    return "fallback"


def get_response(user_input: str, intents: list, state=None) -> str:
    tag = find_intent_tag(user_input, intents)

    if tag == "goodbye":
        return "__EXIT__"

    if tag == "fallback":
        # Try the LLM layer first (returns None if not configured)
        llm_answer = ask_llm(user_input)
        if llm_answer:
            return llm_answer

        # No LLM available (or it also couldn't help) - standard fallback
        if state:
            state.record_fallback()
            if state.fallback_count >= 3:
                state.reset_fallback()
                return ("I'm having trouble understanding a few of your messages. "
                        "Try asking about: admissions, tuition, enrollment, or requirements.")
        return random.choice(get_responses_by_tag("fallback", intents))

    if state:
        state.reset_fallback()

    base_response = random.choice(get_responses_by_tag(tag, intents))

    if tag in PROGRAM_AWARE_INTENTS:
        program = extract_program(user_input)
        if program:
            if state:
                state.remember("program", program)
            base_response = f"[Regarding {program}] " + base_response

    return base_response