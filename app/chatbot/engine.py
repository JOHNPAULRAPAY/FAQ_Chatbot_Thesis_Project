"""
Hybrid chatbot engine: combines rule-based matching (for critical intents
and as a fallback) with ML-based intent classification (for general
recognition). Confidence thresholds decide which result to trust.
"""
import json
import os
import random

from app.chatbot.llm_layer import ask_llm
from app.chatbot.entities import extract_all_entities, list_available_options
from app.chatbot.preprocessing import normalize_text
from app.ml.classifier import load_model, predict_intent

INTENTS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "intents.json"
)

CONFIDENCE_THRESHOLD = 0.5

RULE_ONLY_INTENTS = {"goodbye"}
PROGRAM_AWARE_INTENTS = {"tuition_fees", "admission_requirements", "enrollment_process"}
LEVEL_AWARE_INTENTS = {"admission_requirements"}


def load_intents(path: str = INTENTS_PATH) -> list:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["intents"]


def get_responses_by_tag(tag: str, intents: list) -> list:
    for intent in intents:
        if intent["tag"] == tag:
            return intent["responses"]
    return ["Sorry, I didn't quite understand that. Could you rephrase your question?"]


def get_level_response(tag: str, level: str, intents: list) -> str | None:
    for intent in intents:
        if intent["tag"] == tag:
            level_responses = intent.get("level_responses", {})
            if level in level_responses:
                return "\n".join(level_responses[level])
    return None


def rule_based_match(user_input: str, intents: list) -> str | None:
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


try:
    _vectorizer, _model = load_model()
except FileNotFoundError:
    _vectorizer, _model = None, None


def find_intent_tag(user_input: str, intents: list) -> str:
    rule_tag = rule_based_match(user_input, intents)

    if rule_tag in RULE_ONLY_INTENTS:
        return rule_tag

    if _model is not None:
        ml_tag, confidence = predict_intent(user_input, _vectorizer, _model)
        if confidence >= CONFIDENCE_THRESHOLD and ml_tag not in RULE_ONLY_INTENTS:
            return ml_tag

    if rule_tag is not None:
        return rule_tag

    return "fallback"


def get_response(user_input: str, intents: list, state=None) -> str:
    # --- Check if we're waiting on a clarification from a previous turn ---
    if state:
        awaiting = state.recall("awaiting_clarification")
        if awaiting:
            category = awaiting["entity_category"]
            entities = extract_all_entities(user_input)

            if category not in entities:
                if "program" in entities:
                    entities["admission_level"] = "College"
                elif "shs_strand" in entities:
                    entities["admission_level"] = "Senior High School"

            if category in entities:
                state.remember("awaiting_clarification", None)
                level_reply = get_level_response(awaiting["tag"], entities[category], intents)
                if level_reply:
                    state.remember(category, entities[category])
                    return level_reply

            possible_tag = find_intent_tag(user_input, intents)
            if possible_tag != "fallback":
                state.remember("awaiting_clarification", None)  # they moved on
            else:
                return "I didn't catch that — are you asking about Senior High School or College?"

    tag = find_intent_tag(user_input, intents)

    if tag == "goodbye":
        return "__EXIT__"

    if tag == "program_info":
        programs = list_available_options("program")
        strands = list_available_options("shs_strand")
        return (
            "Here are our available College programs:\n" + "\n".join(f"- {p}" for p in programs) +
            "\n\nAnd our available Senior High School strands:\n" + "\n".join(f"- {s}" for s in strands)
        )

    if tag == "fallback":
        llm_answer = ask_llm(user_input)
        if llm_answer:
            return llm_answer

        if state:
            state.record_fallback()
            if state.fallback_count >= 3:
                state.reset_fallback()
                return ("I'm having trouble understanding a few of your messages. "
                        "Try asking about: admissions, tuition, enrollment, or requirements.")
        return random.choice(get_responses_by_tag("fallback", intents))

    if state:
        state.reset_fallback()

    entities = extract_all_entities(user_input)

    if tag in LEVEL_AWARE_INTENTS and "admission_level" not in entities:
        if "program" in entities:
            entities["admission_level"] = "College"
        elif "shs_strand" in entities:
            entities["admission_level"] = "Senior High School"

    if tag in LEVEL_AWARE_INTENTS and "admission_level" in entities:
        level_reply = get_level_response(tag, entities["admission_level"], intents)
        if level_reply:
            if state:
                state.remember("admission_level", entities["admission_level"])
            return level_reply

    base_response = random.choice(get_responses_by_tag(tag, intents))

    if tag in LEVEL_AWARE_INTENTS and "admission_level" not in entities:
        if state:
            state.remember("awaiting_clarification", {"tag": tag, "entity_category": "admission_level"})

    if tag in PROGRAM_AWARE_INTENTS and "program" in entities:
        program = entities["program"]
        if state:
            state.remember("program", program)
        base_response = f"[Regarding {program}] " + base_response

    return base_response