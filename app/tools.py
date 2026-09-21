# app/tools.py
import re
from langchain_core.tools import tool


@tool
def count_words(text: str) -> int:
    """Counts the number of words in a given text."""
    return len(text.split())


@tool
def check_keyword(text: str, keyword: str) -> dict:
    """
    Checks if a keyword exists in the text (case-insensitive).
    Returns a dictionary indicating if found and the evidence.
    """
    text_lower = text.lower()
    keyword_lower = keyword.lower()

    if keyword_lower in text_lower:
        start = text_lower.index(keyword_lower)
        end = start + len(keyword_lower)
        return {
            "found": True,
            "evidence": {
                "type": "text",
                "quote": text[start:end],
                "start": start,
                "end": end
            }
        }
    return {"found": False, "evidence": None}


@tool
def check_hashtag(text: str, hashtag: str) -> dict:
    """
    Checks if a hashtag (e.g. '#WhopRewards') exists in the text.
    The check is case-insensitive.
    """
    # Normalize: ensure hashtag starts with #
    if not hashtag.startswith("#"):
        hashtag = "#" + hashtag

    text_lower = text.lower()
    hashtag_lower = hashtag.lower()

    if hashtag_lower in text_lower:
        start = text_lower.index(hashtag_lower)
        end = start + len(hashtag_lower)
        return {
            "found": True,
            "evidence": {"quote": text[start:end], "start": start, "end": end}
        }
    return {"found": False, "evidence": None}


@tool
def check_tag(text: str, tag: str) -> dict:
    """
    Checks if an @-tag (e.g. '@jeremygreene') exists in the text.
    The check is case-insensitive.
    """
    if not tag.startswith("@"):
        tag = "@" + tag

    text_lower = text.lower()
    tag_lower = tag.lower()

    if tag_lower in text_lower:
        start = text_lower.index(tag_lower)
        end = start + len(tag_lower)
        return {
            "found": True,
            "evidence": {"quote": text[start:end], "start": start, "end": end}
        }
    return {"found": False, "evidence": None}


@tool
def check_link(text: str, link: str) -> dict:
    """
    Checks if a URL/link exists in the text (case-insensitive).
    """
    text_lower = text.lower()
    link_lower = link.lower()

    if link_lower in text_lower:
        start = text_lower.index(link_lower)
        end = start + len(link_lower)
        return {
            "found": True,
            "evidence": {"quote": text[start:end], "start": start, "end": end}
        }
    return {"found": False, "evidence": None}


@tool
def check_language_english(text: str) -> dict:
    """
    Lightweight heuristic check for English text.
    Checks if common English stop-words are present.
    Not a full NLP language detector — sufficient for this mini-project.
    """
    english_markers = {"the", "is", "and", "to", "of", "a", "in", "that", "it", "for"}
    words = set(text.lower().split())
    matches = english_markers & words
    ratio = len(matches) / len(english_markers) if english_markers else 0.0
    is_english = ratio >= 0.3  # At least 3/10 common English words present
    return {
        "is_english": is_english,
        "evidence": {
            "matched_markers": list(matches),
            "ratio": round(ratio, 2)
        }
    }


@tool
def extract_number(text: str) -> dict:
    """
    Extracts numeric values from a requirement description.
    Useful for parsing 'minimum 10 seconds', 'maximum 50 words', '30%', etc.
    """
    numbers = re.findall(r'\d+(?:\.\d+)?', text)
    return {
        "numbers": [float(n) if '.' in n else int(n) for n in numbers],
        "raw_matches": numbers
    }