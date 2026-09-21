# app/agents/feasibility.py
import re
from app.state import ContentState


def _extract_numeric_constraint(description: str):
    """
    Extract numeric constraints from requirement descriptions.
    Returns (value, unit, constraint_type) or None.
    """
    desc_lower = description.lower()

    # Match patterns like "minimum 10 seconds", "at least 50 words", "maximum 30 seconds"
    patterns = [
        (r"(?:minimum|at least|min)\s+(\d+(?:\.\d+)?)\s*(seconds|words|minutes|%)", "min"),
        (r"(?:maximum|at most|max|under)\s+(\d+(?:\.\d+)?)\s*(seconds|words|minutes|%)", "max"),
        (r"(\d+(?:\.\d+)?)\s*(seconds|words|minutes)\s*(?:long|minimum|min)", "min"),
    ]

    for pattern, constraint_type in patterns:
        match = re.search(pattern, desc_lower)
        if match:
            value = float(match.group(1))
            unit = match.group(2)
            return value, unit, constraint_type

    return None


def _extract_language(description: str):
    """Extract a language requirement from a description."""
    desc_lower = description.lower()
    # Match patterns like "must be in english", "content in spanish", "must be english"
    lang_match = re.search(r"\b(?:must be in|in|be in|be)\s+([a-z]+)\b", desc_lower)
    if lang_match:
        lang = lang_match.group(1)
        valid_languages = {
            'english', 'spanish', 'french', 'german', 'portuguese', 
            'mandarin', 'chinese', 'japanese', 'korean', 'italian', 'russian'
        }
        if lang in valid_languages:
            return lang
    return None


def feasibility_agent(state: ContentState) -> dict:
    """
    Agent 2: Check if the campaign requirements are logically feasible.

    Uses deterministic Python checks for obvious contradictions.
    Does NOT evaluate the content — only the requirements themselves.
    """
    print("--- AGENT: FEASIBILITY CHECKER ---")

    requirements = state["requirements"]
    conflicts = []
    warnings = []

    # ---- Group numeric constraints by unit ----
    constraints_by_unit = {}  # unit -> list of (value, constraint_type, req)
    languages = []

    for req in requirements:
        desc = req["description"]

        # Check numeric constraints
        constraint = _extract_numeric_constraint(desc)
        if constraint:
            value, unit, ctype = constraint
            if unit not in constraints_by_unit:
                constraints_by_unit[unit] = []
            constraints_by_unit[unit].append((value, ctype, req))

        # Check language requirements
        lang = _extract_language(desc)
        if lang:
            languages.append((lang, req))

    # ---- Detect conflicting numeric constraints ----
    for unit, constraints in constraints_by_unit.items():
        mins = [(v, r) for v, t, r in constraints if t == "min"]
        maxs = [(v, r) for v, t, r in constraints if t == "max"]

        for min_val, min_req in mins:
            for max_val, max_req in maxs:
                if min_val > max_val:
                    conflicts.append({
                        "requirements": [min_req["rule"], max_req["rule"]],
                        "reason": f"Minimum {unit} ({min_val}) exceeds maximum {unit} ({max_val})"
                    })

    # ---- Detect conflicting language requirements ----
    if len(languages) > 1:
        unique_langs = set(lang for lang, _ in languages)
        if len(unique_langs) > 1:
            conflicts.append({
                "requirements": [r["rule"] for _, r in languages],
                "reason": f"Conflicting language requirements: {', '.join(unique_langs)}"
            })

    # ---- Check for conflicting boolean rules ----
    # e.g., "comments must stay ON" vs "comments must be OFF"
    comment_states = []
    for req in requirements:
        desc_lower = req["description"].lower()
        if "comments" in desc_lower and "on" in desc_lower:
            comment_states.append(("on", req))
        elif "comments" in desc_lower and "off" in desc_lower:
            comment_states.append(("off", req))

    if len(set(s for s, _ in comment_states)) > 1:
        conflicts.append({
            "requirements": [r["rule"] for _, r in comment_states],
            "reason": "Conflicting comment settings: both ON and OFF required"
        })

    feasible = len(conflicts) == 0

    result = {
        "feasible": feasible,
        "conflicts": conflicts,
        "warnings": warnings,
    }

    status_text = "FEASIBLE" if feasible else "INFEASIBLE"
    print(f"Feasibility: {status_text}")
    if conflicts:
        for c in conflicts:
            print(f"  CONFLICT: {c['reason']}")
    if warnings:
        for w in warnings:
            print(f"  WARNING: {w}")

    return {"feasibility": result}
