# app/agents/analyzer.py
"""
Content Analysis Agent (Agent 3).

For each applicable requirement, produces evidence of whether the content meets it.
- Deterministic requirements: Python tools (exact, fast, trustworthy)
- Semantic requirements: ONE batched Qwen call for all semantic checks
- Non-content requirements (platform/performance/profile/submission): NOT_VERIFIABLE
"""
import re
import json
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from app.llm.provider import get_quality_llm
from app.tools import count_words, check_keyword, check_hashtag, check_tag, check_link, check_language_english
from app.state import ContentState


# --- Pydantic schema for batched semantic analysis ---
class SemanticResult(BaseModel):
    rule: str = Field(description="The rule name being evaluated")
    passed: bool = Field(description="Whether the content meets this requirement")
    evidence: str = Field(description="Specific quotes or observations from the content")
    reason: str = Field(description="Explanation of the judgment")


class SemanticAnalysisResponse(BaseModel):
    results: list[SemanticResult]


# --- Scope-based verifiability check ---
VERIFIABLE_SCOPES = {"content"}  # Only content-scope reqs can be checked from script text


def _is_verifiable(req: dict) -> bool:
    """Check if this requirement can be verified from script text alone."""
    return req.get("scope", "content") in VERIFIABLE_SCOPES


def _check_deterministic(req: dict, content: str) -> dict:
    """
    Evaluate a deterministic requirement using Python tools.
    Returns a standard analysis result dict.
    """
    desc = req["description"]
    desc_lower = desc.lower()
    rule = req["rule"]

    # --- Word count checks ---
    word_count_match = re.search(
        r"(?:minimum|at least|min)\s+(\d+)\s+words", desc_lower
    )
    if word_count_match:
        target = int(word_count_match.group(1))
        actual = count_words.invoke({"text": content})
        passed = actual >= target
        return {
            "requirement": rule,
            "description": desc,
            "passed": passed,
            "evidence": f"Word count: {actual}",
            "reason": f"{'Meets' if passed else 'Does not meet'} minimum {target} words (actual: {actual})"
        }

    max_word_match = re.search(
        r"(?:maximum|at most|max|under)\s+(\d+)\s+words", desc_lower
    )
    if max_word_match:
        target = int(max_word_match.group(1))
        actual = count_words.invoke({"text": content})
        passed = actual <= target
        return {
            "requirement": rule,
            "description": desc,
            "passed": passed,
            "evidence": f"Word count: {actual}",
            "reason": f"{'Meets' if passed else 'Exceeds'} maximum {target} words (actual: {actual})"
        }

    # --- Language check ---
    if "english" in desc_lower and ("must be" in desc_lower or "in english" in desc_lower):
        result = check_language_english.invoke({"text": content})
        return {
            "requirement": rule,
            "description": desc,
            "passed": result["is_english"],
            "evidence": f"English markers found: {result['evidence']['matched_markers']}",
            "reason": f"Language check ratio: {result['evidence']['ratio']}"
        }

    # --- Hashtag check ---
    hashtag_match = re.search(r"(#\w+)", desc)
    if hashtag_match:
        hashtag = hashtag_match.group(1)
        result = check_hashtag.invoke({"text": content, "hashtag": hashtag})
        return {
            "requirement": rule,
            "description": desc,
            "passed": result["found"],
            "evidence": f"Hashtag '{hashtag}' {'found' if result['found'] else 'not found'} in content",
            "reason": f"Searched for exact hashtag {hashtag}"
        }

    # --- Tag check ---
    tag_match = re.search(r"(@\w+)", desc)
    if tag_match:
        tag = tag_match.group(1)
        result = check_tag.invoke({"text": content, "tag": tag})
        return {
            "requirement": rule,
            "description": desc,
            "passed": result["found"],
            "evidence": f"Tag '{tag}' {'found' if result['found'] else 'not found'} in content",
            "reason": f"Searched for exact tag {tag}"
        }

    # --- Link check ---
    link_match = re.search(r"(https?://\S+)", desc)
    if link_match:
        link = link_match.group(1)
        result = check_link.invoke({"text": content, "link": link})
        return {
            "requirement": rule,
            "description": desc,
            "passed": result["found"],
            "evidence": f"Link '{link}' {'found' if result['found'] else 'not found'} in content",
            "reason": f"Searched for exact link"
        }

    # --- Keyword mention check (generic "must mention X") ---
    mention_match = re.search(r"must\s+mention\s+(.+?)(?:\.|$)", desc_lower)
    if mention_match:
        keyword = mention_match.group(1).strip()
        result = check_keyword.invoke({"text": content, "keyword": keyword})
        return {
            "requirement": rule,
            "description": desc,
            "passed": result["found"],
            "evidence": f"Keyword '{keyword}' {'found' if result['found'] else 'not found'} in content",
            "reason": f"Searched for mention of '{keyword}'"
        }

    # --- Generic keyword inclusion ("must include X") ---
    include_match = re.search(r"must\s+include\s+(.+?)(?:\.|$)", desc_lower)
    if include_match:
        keyword = include_match.group(1).strip()
        # Check if it's a tag/hashtag/link already handled above
        if not keyword.startswith(("#", "@", "http")):
            result = check_keyword.invoke({"text": content, "keyword": keyword})
            return {
                "requirement": rule,
                "description": desc,
                "passed": result["found"],
                "evidence": f"'{keyword}' {'found' if result['found'] else 'not found'} in content",
                "reason": f"Searched for inclusion of '{keyword}'"
            }

    # --- Fallback: deterministic type but no matching tool ---
    return {
        "requirement": rule,
        "description": desc,
        "passed": None,
        "evidence": "No deterministic check available for this requirement",
        "reason": "DEFERRED — deterministic check not implemented for this pattern",
        "status": "DEFERRED"
    }


def _check_semantic_batch(semantic_reqs: list[dict], content: str, raw_requirements: str) -> list[dict]:
    """
    Evaluate ALL semantic requirements in ONE Qwen call.
    Returns a list of analysis result dicts.
    """
    if not semantic_reqs:
        return []

    print(f"  Evaluating {len(semantic_reqs)} semantic requirements in one LLM call...")

    llm = get_quality_llm(temperature=0.3)
    structured_llm = llm.with_structured_output(SemanticAnalysisResponse)

    # Build the requirements list for the prompt
    req_list = "\n".join(
        f"- {req['rule']}: {req['description']}"
        for req in semantic_reqs
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a content evaluator. Given campaign requirements and a content script, "
         "evaluate whether the script meets each semantic requirement.\n\n"
         "For each requirement, provide:\n"
         "- rule: the rule name\n"
         "- passed: true/false\n"
         "- evidence: specific quotes or observations from the content\n"
         "- reason: your judgment explanation\n\n"
         "Be fair but strict. Base your judgment only on what is actually in the content. "
         "Do not hallucinate content that isn't there."),
        ("human",
         "CAMPAIGN CONTEXT:\n{raw_requirements}\n\n"
         "REQUIREMENTS TO EVALUATE:\n{req_list}\n\n"
         "CONTENT SCRIPT:\n{content}")
    ])

    chain = prompt | structured_llm
    result = chain.invoke({
        "raw_requirements": raw_requirements,
        "req_list": req_list,
        "content": content
    })

    # Convert to standard format
    analysis_results = []
    for sr in result.results:
        analysis_results.append({
            "requirement": sr.rule,
            "description": next(
                (r["description"] for r in semantic_reqs if r["rule"] == sr.rule),
                ""
            ),
            "passed": sr.passed,
            "evidence": sr.evidence,
            "reason": sr.reason,
        })

    return analysis_results


def analyzer_agent(state: ContentState) -> dict:
    """
    Agent 3: Analyze content against each requirement.

    - Deterministic requirements → Python tools (instant)
    - Semantic requirements → ONE batched Qwen call
    - Non-verifiable requirements → NOT_VERIFIABLE status
    """
    print("--- AGENT: CONTENT ANALYZER ---")

    requirements = state["requirements"]
    content = state["content"]
    raw_requirements = state.get("raw_requirements", "")

    all_results = []
    semantic_reqs = []

    for req in requirements:
        # Check if there's a condition — if so, note it but still evaluate
        # (In this mini-project, we evaluate all; conditions are informational)
        condition = req.get("condition")

        # Non-verifiable scopes
        if not _is_verifiable(req):
            all_results.append({
                "requirement": req["rule"],
                "description": req["description"],
                "passed": None,
                "evidence": f"Cannot verify from script (scope: {req['scope']})",
                "reason": "NOT_VERIFIABLE — requires platform/performance/profile/submission data",
                "status": "NOT_VERIFIABLE",
                "condition": condition,
            })
            continue

        if req["type"] == "deterministic":
            result = _check_deterministic(req, content)
            result["condition"] = condition
            all_results.append(result)
        elif req["type"] == "semantic":
            semantic_reqs.append(req)
        else:
            all_results.append({
                "requirement": req["rule"],
                "description": req["description"],
                "passed": None,
                "evidence": "Unknown requirement type",
                "reason": "DEFERRED",
                "status": "DEFERRED",
                "condition": condition,
            })

    # Batch all semantic requirements into one LLM call
    semantic_results = _check_semantic_batch(semantic_reqs, content, raw_requirements)
    for sr in semantic_results:
        # Find the matching req for condition info
        matching_req = next((r for r in semantic_reqs if r["rule"] == sr["requirement"]), {})
        sr["condition"] = matching_req.get("condition")
        all_results.append(sr)

    # Summary
    passed = sum(1 for r in all_results if r.get("passed") is True)
    failed = sum(1 for r in all_results if r.get("passed") is False)
    deferred = sum(1 for r in all_results if r.get("passed") is None)
    print(f"Analysis complete: {passed} passed, {failed} failed, {deferred} deferred/not-verifiable")

    return {"analysis": all_results}
