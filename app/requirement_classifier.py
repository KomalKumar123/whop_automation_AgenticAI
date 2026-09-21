# app/requirement_classifier.py
import re


def classify_requirement(description: str) -> str:
    """
    Determines if a requirement can be validated deterministically (via Python tools)
    or semantically (via LLM).

    Python is authoritative — the LLM must NOT override this.
    """
    desc_lower = description.lower()

    # Patterns that indicate deterministic validation
    deterministic_patterns = [
        # Numeric constraints (word count, duration, etc.)
        r"(?:minimum|at least|min)\s+\d+\s+(?:words|seconds|minutes)",
        r"(?:maximum|at most|max|under)\s+\d+\s+(?:words|seconds|minutes)",
        r"exactly\s+\d+\s+(?:words|seconds|minutes)",
        # Exact mention / inclusion
        r"must\s+(?:mention|include|contain)",
        r"must\s+be\s+in\s+\w+",               # "must be in English"
        r"must\s+tag\b",
        r"must\s+stay\s+on",                    # "comments must stay ON"
        # Hashtags, tags, links
        r"include\s+the\s+hashtag",
        r"include\s+the\s+link",
        r"tag\s+@",
        r"#\w+",                                 # literal hashtag reference
        r"@\w+",                                 # literal tag reference
        # Explicit prohibitions with clear binary check
        r"no\s+paid\s+boost",
        r"no\s+story\s+boost",
        # Language requirement
        r"(?:content|video|script)\s+must\s+be\s+in\s+\w+",
        r"must\s+be\s+in\s+english",
        r"in\s+english",
        # Numeric audience thresholds
        r"minimum\s+\d+%",
        r"at\s+least\s+\d+\s+seconds",
        # Profile / submission requirements
        r"description\s+must\s+mention",
        r"profile\s+description\s+must",
        r"provide\s+the\s+source",
        r"source\s+link",
    ]

    for pattern in deterministic_patterns:
        if re.search(pattern, desc_lower):
            return "deterministic"

    # Default to semantic for subjective requirements
    return "semantic"