# app/state.py
from typing import TypedDict, Any


class ContentState(TypedDict, total=False):
    # Original inputs
    original_content: str
    content: str
    raw_requirements: str

    # Extracted campaign requirements
    requirements: list[dict[str, Any]]

    # Requirement feasibility
    feasibility: dict[str, Any]

    # Content analysis
    analysis: list[dict[str, Any]]

    # Mandatory compliance
    compliance: dict[str, Any]

    # Content quality
    quality: dict[str, Any]

    # Improvement
    improvements: dict[str, Any]

    # Revision tracking
    revision_count: int
    revision_history: list[dict[str, Any]]

    # Final decision: APPROVED, NEEDS_IMPROVEMENT, HUMAN_REVIEW_REQUIRED
    decision: str