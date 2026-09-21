# app/graph.py
"""
LangGraph Orchestrator (Phase 10).

Builds the StateGraph representing the multi-agent workflow:
Requirement -> Feasibility -> [Feasible?]
                                 ├── No  → HUMAN_REVIEW_REQUIRED (END)
                                 └── Yes → Analyzer -> Compliance -> Quality -> [Approved?]
                                                                                  ├── Yes → APPROVED (END)
                                                                                  └── No  → [Max Revisions?]
                                                                                               ├── Yes → HUMAN_REVIEW_REQUIRED (END)
                                                                                               └── No  → Improvement -> Analyzer (Loop)
"""
from langgraph.graph import StateGraph, END
from app.state import ContentState

from app.agents.requirements import requirement_agent
from app.agents.feasibility import feasibility_agent
from app.agents.analyzer import analyzer_agent
from app.agents.compliance import compliance_agent
from app.agents.quality import quality_agent
from app.agents.improvement import improvement_agent


def route_feasibility(state: ContentState) -> str:
    """Routes based on campaign requirements feasibility."""
    feasibility = state.get("feasibility", {})
    if not feasibility.get("feasible", True):
        return "infeasible"
    return "feasible"


def handle_infeasible_termination(state: ContentState) -> dict:
    """Terminal node for infeasible campaign."""
    print("Workflow routing: INFEASIBLE. Terminating.")
    return {"decision": "HUMAN_REVIEW_REQUIRED"}


def route_approval(state: ContentState) -> str:
    """Routes based on compliance and quality scoring."""
    compliance = state.get("compliance", {})
    quality = state.get("quality", {})
    
    compliance_passed = compliance.get("status") == "PASS"
    overall_score = quality.get("overall_score", 0.0)
    revision_count = state.get("revision_count", 0)
    
    print(f"Approval Route Decision: Compliance={compliance.get('status')}, Quality={overall_score}, Revision={revision_count}")
    
    if compliance_passed and overall_score >= 8.0:
        return "approved"
        
    # If not approved, check revision limits
    if revision_count >= 3:
        return "max_revisions"
        
    return "needs_improvement"


def handle_approved_termination(state: ContentState) -> dict:
    """Terminal node for approved script."""
    print("Workflow routing: APPROVED. Terminating.")
    return {"decision": "APPROVED"}


def handle_max_revisions_termination(state: ContentState) -> dict:
    """Terminal node when revision limit is reached without approval."""
    print("Workflow routing: MAX REVISIONS REACHED. Terminating.")
    return {"decision": "HUMAN_REVIEW_REQUIRED"}


def build_workflow() -> StateGraph:
    """Builds and compiles the StateGraph."""
    workflow = StateGraph(ContentState)
    
    # 1. Define nodes
    workflow.add_node("requirement_agent", requirement_agent)
    workflow.add_node("feasibility_agent", feasibility_agent)
    workflow.add_node("analyzer_agent", analyzer_agent)
    workflow.add_node("compliance_agent", compliance_agent)
    workflow.add_node("quality_agent", quality_agent)
    workflow.add_node("improvement_agent", improvement_agent)
    
    # Termination helpers
    workflow.add_node("handle_infeasible", handle_infeasible_termination)
    workflow.add_node("handle_approved", handle_approved_termination)
    workflow.add_node("handle_max_revisions", handle_max_revisions_termination)
    
    # 2. Define edges and routing
    # Starting flow
    workflow.set_entry_point("requirement_agent")
    workflow.add_edge("requirement_agent", "feasibility_agent")
    
    # Feasibility conditional routing
    workflow.add_conditional_edges(
        "feasibility_agent",
        route_feasibility,
        {
            "feasible": "analyzer_agent",
            "infeasible": "handle_infeasible"
        }
    )
    
    # Linear analysis and scoring block
    workflow.add_edge("analyzer_agent", "compliance_agent")
    workflow.add_edge("compliance_agent", "quality_agent")
    
    # Approval / revision conditional routing
    workflow.add_conditional_edges(
        "quality_agent",
        route_approval,
        {
            "approved": "handle_approved",
            "max_revisions": "handle_max_revisions",
            "needs_improvement": "improvement_agent"
        }
    )
    
    # Loop from improvement back to re-analyze
    workflow.add_edge("improvement_agent", "analyzer_agent")
    
    # Connect termination nodes to END
    workflow.add_edge("handle_infeasible", END)
    workflow.add_edge("handle_approved", END)
    workflow.add_edge("handle_max_revisions", END)
    
    # Compile the graph
    return workflow.compile()
