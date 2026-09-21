# app/main.py
"""
CLI Entry Point (Phase 11).

Loads campaign.txt and content.txt, runs the LangGraph evaluation workflow,
and pretty-prints the steps, revisions, and final outcome.
"""
import os
import sys
from dotenv import load_dotenv
from app.graph import build_workflow

def load_file_content(path: str) -> str:
    """Helper to safely read file content."""
    if not os.path.exists(path):
        print(f"Error: Required file not found at {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def run_evaluation(campaign_path: str = "data/campaign.txt", content_path: str = "data/content.txt"):
    # Load environment variables
    load_dotenv()
    
    print("=" * 50)
    print("CAMPAIGN-AWARE CONTENT EVALUATOR & OPTIMIZER")
    print("=" * 50)
    
    # 1. Read files
    raw_campaign = load_file_content(campaign_path)
    raw_content = load_file_content(content_path)
    
    print(f"Loaded campaign from: {campaign_path}")
    print(f"Loaded content from: {content_path}")
    print(f"Content length: {len(raw_content.split())} words, {len(raw_content)} chars.")
    print("-" * 50)
    
    # 2. Setup initial state
    initial_state = {
        "original_content": raw_content,
        "content": raw_content,
        "raw_requirements": raw_campaign,
        "requirements": [],
        "revision_count": 0,
        "revision_history": []
    }
    
    # 3. Compile and invoke workflow
    app = build_workflow()
    
    print("Executing evaluation workflow graph...")
    final_state = app.invoke(initial_state)
    print("-" * 50)
    
    # 4. Print final output summary
    print("=" * 50)
    print("EVALUATION RUN COMPLETE")
    print("=" * 50)
    
    # Requirements summary
    reqs = final_state.get("requirements", [])
    print(f"Requirements Extracted: {len(reqs)}")
    
    # Feasibility status
    feasibility = final_state.get("feasibility", {})
    feasible = "FEASIBLE" if feasibility.get("feasible") else "INFEASIBLE"
    print(f"Campaign Feasibility: {feasible}")
    if not feasibility.get("feasible"):
        print("Conflicts found:")
        for c in feasibility.get("conflicts", []):
            print(f"  - {c['reason']} (Rules involved: {', '.join(c['requirements'])})")
            
    # If feasibility check failed, exit early
    if not feasibility.get("feasible"):
        print("\nWorkflow ended early due to Campaign Infeasibility.")
        print(f"DECISION: {final_state.get('decision')}")
        print("=" * 50)
        return
        
    # Analysis check-by-check
    print("\nCONTENT ANALYSIS RESULTS:")
    analysis = final_state.get("analysis", [])
    for res in sorted(analysis, key=lambda x: x["requirement"]):
        passed = res.get("passed")
        status = res.get("status")
        
        icon = "[PASS]" if passed is True else "[FAIL]" if passed is False else "[WARN]"
        val_type = " [Semantic]" if res.get("type") == "semantic" else " [Deterministic]"
        
        print(f"{icon} {res['requirement']}{val_type}")
        print(f"  Description: {res['description']}")
        print(f"  Evidence: {res.get('evidence')}")
        print(f"  Reason: {res.get('reason')}")
        if res.get("condition"):
            print(f"  Condition: {res['condition']}")
        print()
        
    # Compliance Status
    compliance = final_state.get("compliance", {})
    print(f"MANDATORY COMPLIANCE: {compliance.get('status')}")
    if compliance.get("failed_requirements"):
        print("Failed content rules:")
        for f in compliance["failed_requirements"]:
            print(f"  - {f['rule']}: {f['description']}")
    if compliance.get("deferred_requirements"):
        print("Deferred platform/performance rules:")
        for d in compliance["deferred_requirements"]:
            print(f"  - {d['rule']}: {d['description']} ({d['reason']})")
            
    # Content Quality
    quality = final_state.get("quality", {})
    print(f"\nCONTENT QUALITY SCORES:")
    for key, val in quality.items():
        if key not in ["weaknesses", "confidence", "overall_score"]:
            print(f"  {key.replace('_', ' ').title()}: {val}/10")
    print(f"  Overall Quality Score: {quality.get('overall_score')}/10")
    if quality.get("weaknesses"):
        print("Quality Weaknesses:")
        for w in quality["weaknesses"]:
            print(f"  - {w}")
            
    # Revisions history
    history = final_state.get("revision_history", [])
    print(f"\nRevisions performed: {final_state.get('revision_count', 0)}")
    for i, rev in enumerate(history, 1):
        print(f"  Revision {i}:")
        print(f"    Reasoning score before: {rev['quality_before']}")
        print(f"    Changes made:")
        for ch in rev["changes_made"]:
            print(f"      - {ch}")
            
    # Final Decision
    print(f"\nFINAL DECISION: {final_state.get('decision')}")
    print("-" * 50)
    print("FINAL SCRIPT:")
    print(final_state.get("content"))
    print("=" * 50)

if __name__ == "__main__":
    run_evaluation()
