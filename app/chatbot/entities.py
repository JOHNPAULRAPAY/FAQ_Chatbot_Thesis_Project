"""
Entity extraction: detects known entities mentioned in user messages,
using spaCy's PhraseMatcher with custom term lists per category.

To add a NEW entity category later (e.g. campus, year level, semester):
just add a new key to ENTITY_DEFINITIONS below, following the same
{canonical_name: [aliases]} shape.
"""
import spacy
from spacy.matcher import PhraseMatcher

_nlp = spacy.load("en_core_web_sm")

ENTITY_DEFINITIONS = {
    "program": {
        "Accounting Information Technology": ["accounting information technology", "ait", "bsait"],
        "Computer Science": ["comsci", "computer science", "cs", "bscs"],
        "Entrepreneurship": ["entrepreneurship", "entrep", "entrepreneur", "bse"],
        "Associate in Computer Technology": ["associate in computer technology", "associate computer technology", "act"],
    },
    "shs_strand": {
        "STEM": ["stem", "science technolgy engineering and mathematics"],
        "ABM": ["abm", "accountancy business and management"],
        "HUMSS": ["humss", "humanities and social science"],
        "GAS": ["gas", "general academic strand"],
        "ICT": ["ict", "information and communication technolgy"]
    },
    "admission_level": {
        "Senior High School": ["shs", "senior high school", "senior high", "grade 11", "grade 12"],
        "College": ["college", "tertiary", "undergraduate", "bachelors degree", "bachelor"],
    },
}

# One PhraseMatcher per category, so categories never collide with each other
_matchers = {}

for category, entities in ENTITY_DEFINITIONS.items():
    matcher = PhraseMatcher(_nlp.vocab, attr="LOWER")
    for canonical_name, aliases in entities.items():
        patterns = [_nlp.make_doc(alias) for alias in aliases]
        matcher.add(canonical_name, patterns)
    _matchers[category] = matcher


def extract_entity(text: str, category: str) -> str | None:
    """
    Scans text for a known entity within one category (e.g. 'program').
    Returns the canonical name if found, or None.
    """
    if category not in _matchers:
        return None

    doc = _nlp(text.lower())
    matches = _matchers[category](doc)

    if not matches:
        return None

    match_id, start, end = matches[0]
    return _nlp.vocab.strings[match_id]


def extract_all_entities(text: str) -> dict:
    """
    Runs extraction across ALL categories at once.
    Returns e.g. {"program": "Computer Science", "admission_level": "College"}
    (keys with no match are omitted).
    """
    doc_lower = text.lower()
    doc = _nlp(doc_lower)

    found = {}
    for category, matcher in _matchers.items():
        matches = matcher(doc)
        if matches:
            match_id, start, end = matches[0]
            found[category] = _nlp.vocab.strings[match_id]

    return found

def list_available_options(category: str) -> list:
    """
    Returns the canonical names of all known entities in a category
    (e.g. all college programs, or all SHS strands). Used to tell users
    what's available when they ask, or when their input isn't recognized.
    """
    return list(ENTITY_DEFINITIONS.get(category, {}).keys())