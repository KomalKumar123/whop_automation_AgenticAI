# app/agents/requirements.py
"""
Requirement Agent (Agent 1).

Extracts structured requirements from raw campaign text.

Strategy: Because Llama 3.2:1b struggles with complex structured output
for long documents, we use a two-step approach:
  1. LLM extracts requirements as a simple numbered list (text)
  2. Python parses the list into structured format and adds type/scope/condition
"""
import re
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.llm.provider import get_fast_llm
from app.requirement_classifier import classify_requirement
from app.state import ContentState


# --- Valid scopes ---
VALID_SCOPES = {"content", "platform", "performance", "profile", "submission"}


def _normalize_scope(description: str) -> str:
    """
    Deterministically assign scope based on description keywords.
    """
    desc_lower = description.lower()

    submission_keywords = [
        "source link", "provide the source", "submission",
    ]
    profile_keywords = [
        "profile description", "description must mention",
    ]
    performance_keywords = [
        "tier-1", "tier 1", "audience", "30%",
    ]
    platform_keywords = [
        "tag @", "must tag", "@jeremygreene", "@jeremy",
        "hashtag", "#whoprewards",
        "caption",
        "comments must", "comments stay",
        "no paid boost", "no story boost",
        "paid boosting", "story boosting",
    ]

    for kw in submission_keywords:
        if kw in desc_lower:
            return "submission"
    for kw in profile_keywords:
        if kw in desc_lower:
            return "profile"
    for kw in performance_keywords:
        if kw in desc_lower:
            return "performance"
    for kw in platform_keywords:
        if kw in desc_lower:
            return "platform"

    return "content"


def _extract_condition(description: str) -> tuple[Optional[str], str]:
    """
    Extract condition and clean the description.
    Returns (condition, cleaned_description).
    """
    desc = description.strip()
    match = re.match(r"^[Ii]f\s+(posting\s+.+?):\s*(.+)$", desc)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    # Also handle "If posting X, ..."
    match2 = re.match(r"^[Ii]f\s+(posting\s+.+?),\s*(.+)$", desc)
    if match2:
        return match2.group(1).strip(), match2.group(2).strip()
    return None, desc


def _make_rule_name(description: str) -> str:
    """Generate a snake_case rule name from a description."""
    # Common rule name mappings
    desc_lower = description.lower()
    mappings = [
        ("at least 10 seconds", "min_video_length"),
        ("at least", "min_length"),
        ("must be in english", "language"),
        ("in english", "language"),
        ("positioned positively", "positive_portrayal"),
        ("create curiosity", "curiosity"),
        ("tier-1 audience", "tier1_audience"),
        ("30%", "tier1_audience"),
        ("comments must stay", "comments_on"),
        ("no paid boost", "no_paid_boosting"),
        ("no story boost", "no_story_boosting"),
        ("tag @jeremygreene", "tag_jeremygreene"),
        ("must tag", "required_tag"),
        ("#whoprewards", "hashtag_whoprewards"),
        ("hashtag", "required_hashtag"),
        ("call to action", "cta_caption"),
        ("engaging", "engaging_caption"),
        ("podcast", "podcast_caption"),
        ("documentary", "documentary_title"),
        ("profile description", "profile_description"),
        ("source link", "source_link"),
        ("provide the source", "source_link"),
        ("link in bio", "cta_caption"),
    ]

    for keyword, rule_name in mappings:
        if keyword in desc_lower:
            return rule_name

    # Fallback: generate from first few words
    words = re.findall(r'[a-z]+', desc_lower)[:4]
    return "_".join(words) if words else "unknown_rule"


def _is_section_header(text: str) -> bool:
    """Check if a line is a section header rather than a requirement."""
    stripped = text.strip()
    # Lines that end with ':' and have no verb are likely section headers
    if stripped.endswith(":") and len(stripped.split()) <= 5:
        return True
    return False


def _parse_numbered_list(text: str) -> list[str]:
    """Parse a numbered or bulleted list from LLM output."""
    lines = text.strip().split("\n")
    items = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Remove numbering: "1. ", "1) ", "- ", "* "
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", line)
        cleaned = re.sub(r"^[-*]\s*", "", cleaned)
        cleaned = cleaned.strip()
        if cleaned and len(cleaned) > 5 and not _is_section_header(cleaned):
            items.append(cleaned)
    return items


def _extract_bullet_points(text: str) -> list[str]:
    """Deterministically extract bullet points and numbered list items from text."""
    lines = text.strip().split("\n")
    bullets = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Matches "- text", "* text", "1. text", "1) text"
        if re.match(r"^[-*]\s+", line) or re.match(r"^\d+[\.\)]\s+", line):
            cleaned = re.sub(r"^[-*]\s*", "", line)
            cleaned = re.sub(r"^\d+[\.\)]\s*", "", cleaned)
            cleaned = cleaned.strip()
            if cleaned and len(cleaned) > 5 and not _is_section_header(cleaned):
                bullets.append(cleaned)
    return bullets


def requirement_agent(state: ContentState) -> dict:
    """
    Agent 1: Extract structured requirements from raw campaign text.

    Uses a hybrid approach:
    1. Asks Llama 1B to extract requirements.
    2. Deterministically parses raw bullet points in python.
    3. Merges and deduplicates the two lists.
    """
    print("--- AGENT: REQUIREMENT PARSER ---")
    llm = get_fast_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "List every distinct rule from the campaign as a numbered list. "
         "One rule per line. Keep the original wording. "
         "Include conditional rules (If posting...). "
         "Include profile and source link rules."),
        ("human", "{raw_requirements}")
    ])

    chain = prompt | llm | StrOutputParser()

    print("Invoking LLM to extract requirements...")
    raw_output = ""
    try:
        raw_output = chain.invoke({"raw_requirements": state["raw_requirements"]})
        print(f"RAW LLM OUTPUT:\n{raw_output}\n---")
        llm_items = _parse_numbered_list(raw_output)
    except Exception as e:
        print(f"LLM extraction failed: {e}. Falling back to Python parsing.")
        llm_items = []

    # Deterministic fallback/addition
    python_items = _extract_bullet_points(state["raw_requirements"])
    
    # Merge and deduplicate based on clean lowercased content
    merged_items = []
    seen_texts = set()
    
    # Helper to normalize text for deduplication
    def normalize_text(t):
        return re.sub(r'\W+', '', t.lower())
        
    for item in python_items + llm_items:
        norm = normalize_text(item)
        if norm not in seen_texts:
            seen_texts.add(norm)
            merged_items.append(item)

    print(f"Requirements found: {len(python_items)} via Python, {len(llm_items)} via LLM. Merged to {len(merged_items)} distinct items.")

    # Build structured requirements with Python-derived fields
    final_requirements = []
    seen_rules = set()

    for desc in merged_items:
        # Extract condition
        condition, clean_desc = _extract_condition(desc)

        # Generate rule name
        rule = _make_rule_name(clean_desc)

        # Deduplicate rule names
        if rule in seen_rules:
            rule = f"{rule}_{len(seen_rules)}"
        seen_rules.add(rule)

        req_dict = {
            "rule": rule,
            "description": clean_desc,
            "type": classify_requirement(clean_desc),
            "scope": _normalize_scope(clean_desc),
            "condition": condition,
        }
        final_requirements.append(req_dict)

    print(f"Structured {len(final_requirements)} requirements.")

    return {"requirements": final_requirements}