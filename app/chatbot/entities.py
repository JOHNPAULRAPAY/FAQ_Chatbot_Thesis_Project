"""
Entity extraction: detects known entities (currently: academic program
names) mentioned in user messages, using spaCy's PhraseMatcher with a
custom list of terms specific to this school.
"""
import spacy
from spacy.matcher import PhraseMatcher

_nlp = spacy.load("en_core_web_sm")

# EDIT THIS LIST with your school's actual program names and common
# abbreviations/aliases students might type for each.
PROGRAMS = {
    "Accounting Information Technology": ["accounting information technology", "ait", "bsait"],
    "Computer Science": ["comsci", "computer science", "cs"],
    "Entrepreneurship": ["entrepreneurship", "entrep", "entrepreneur"],
    "Associate in Computer Technology": ["associate in computer technology", "associate computer technology", "act"],
}

_matcher = PhraseMatcher(_nlp.vocab, attr="LOWER")

for program_name, aliases in PROGRAMS.items():
    patterns = [_nlp.make_doc(alias) for alias in aliases]
    _matcher.add(program_name, patterns)


def extract_program(text: str) -> str | None:
    """
    Scans text for a known program name/alias. Returns the canonical
    program name if found (e.g. "bsit" -> "Information Technology"),
    or None if no program is mentioned.
    """
    doc = _nlp(text.lower())
    matches = _matcher(doc)

    if not matches:
        return None

    match_id, start, end = matches[0]  # take the first match found
    canonical_name = _nlp.vocab.strings[match_id]
    return canonical_name