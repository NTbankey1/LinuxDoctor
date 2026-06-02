"""
Text Processing Engine — Phase 1.

Implements tokenization, stopword removal, and rule-based stemming
from scratch without any NLP library (no NLTK, no spaCy).
"""

import re
from typing import Final

# ---------------------------------------------------------------------------
# 1. STOPWORDS (Linux-aware — preserve technical error terms)
# ---------------------------------------------------------------------------

STOPWORDS: Final[frozenset[str]] = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "need", "this", "that", "these",
    "those", "i", "my", "your", "his", "her", "its", "our", "their",
    "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
    "into", "through", "during", "before", "after", "if", "then",
    "and", "or", "but", "so", "yet", "nor", "not", "also", "just",
    "when", "while", "because", "how", "what", "which", "who",
    "up", "out", "about", "against", "over", "again",
    "try", "trying", "get", "getting", "got", "run", "running",
})

# Technical terms that must NEVER be removed as stopwords
PRESERVE_TERMS: Final[frozenset[str]] = frozenset({
    "denied", "refused", "failed", "error", "warning", "permission",
    "timeout", "kill", "killed", "crash", "down", "dead", "missing",
})

# ---------------------------------------------------------------------------
# 2. PORTER-LITE STEMMER (rule-based suffix stripping)
# ---------------------------------------------------------------------------

# Order matters: longer suffixes first
_SUFFIX_RULES: Final[list[tuple[str, str, int]]] = [
    # (suffix_to_remove, replacement, min_stem_length)
    ("ication", "ic",   4),
    ("ational", "ate",  4),
    ("fulness", "",     4),
    ("ousness", "",     4),
    ("iveness", "",     4),
    ("ations",  "",     4),
    ("nesses",  "",     4),
    ("abling",  "able", 2),
    ("inging",  "ing",  2),
    ("ating",   "ate",  3),
    ("izing",   "ize",  3),
    ("izing",   "ize",  3),
    ("izing",   "ize",  3),
    ("nesses",  "",     4),
    ("ation",   "ate",  4),
    ("ness",    "",     4),
    ("ment",    "",     4),
    ("less",    "",     4),
    ("able",    "",     4),
    ("ible",    "",     4),
    ("ical",    "",     4),
    ("ance",    "",     4),
    ("ence",    "",     4),
    ("ting",    "t",    3),
    ("ning",    "n",    3),
    ("ring",    "r",    3),
    ("sing",    "s",    3),
    ("ding",    "d",    3),
    ("king",    "k",    3),
    ("ing",     "",     4),
    ("tion",    "",     4),
    ("sion",    "",     4),
    ("tions",   "",     4),
    ("ions",    "",     3),
    ("ies",     "y",    3),
    ("ied",     "y",    3),
    ("ers",     "er",   3),
    ("ed",      "",     4),
    ("er",      "",     4),
    ("ly",      "",     4),
    ("al",      "",     4),
    ("es",      "",     3),
    ("s",       "",     4),
]


def stem(word: str) -> str:
    """
    Apply rule-based suffix stripping (Porter-lite).

    Args:
        word: A single lowercase word token.

    Returns:
        The stemmed form of the word.
    """
    # Never stem short words or preserved technical terms
    if len(word) <= 3 or word in PRESERVE_TERMS:
        return word

    for suffix, replacement, min_len in _SUFFIX_RULES:
        if word.endswith(suffix) and len(word) - len(suffix) >= min_len:
            return word[: -len(suffix)] + replacement

    return word


# ---------------------------------------------------------------------------
# 3. TOKENIZER
# ---------------------------------------------------------------------------

# Regex: match words made of alphanumeric + hyphen (keep "docker-compose")
_TOKEN_PATTERN: Final[re.Pattern[str]] = re.compile(r"[a-z][a-z0-9\-]*[a-z0-9]|[a-z]")


def tokenize(text: str) -> list[str]:
    """
    Tokenize text into lowercase alphabetic tokens.

    Steps:
    1. Lowercase
    2. Replace IP addresses, paths, hex with placeholder
    3. Extract word tokens via regex

    Args:
        text: Raw input string.

    Returns:
        List of lowercase tokens.
    """
    text = text.lower()

    # Normalize known noise patterns
    text = re.sub(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", "ipaddr", text)  # IPs
    text = re.sub(r"0x[0-9a-f]+", "hexval", text)                   # hex
    text = re.sub(r"/[\w/\.\-]+", lambda m: m.group().split("/")[-1], text)  # paths

    return _TOKEN_PATTERN.findall(text)


# ---------------------------------------------------------------------------
# 4. FULL PIPELINE
# ---------------------------------------------------------------------------


def preprocess(text: str, apply_stemming: bool = True) -> list[str]:
    """
    Complete preprocessing pipeline.

    Tokenize → Remove Stopwords → Stem (optional).

    Args:
        text: Raw input string.
        apply_stemming: Whether to apply Porter-lite stemming.

    Returns:
        List of processed tokens.
    """
    tokens = tokenize(text)
    tokens = [t for t in tokens if t not in STOPWORDS or t in PRESERVE_TERMS]
    if apply_stemming:
        tokens = [stem(t) for t in tokens]
    return tokens


def preprocess_to_string(text: str, apply_stemming: bool = True) -> str:
    """Preprocess and return as a space-joined string (for TF-IDF input)."""
    return " ".join(preprocess(text, apply_stemming))
