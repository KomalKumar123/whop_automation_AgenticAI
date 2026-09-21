# app/agents/compliance.py
"""
Compliance Agent (Agent 4).

Judges mandatory content compliance based on analysis evidence.
Does not redo the analysis.
Groups non-verifiable requirements as DEFERRED.
"""
from app.state import ContentState

def compliance_agent(state: ContentState) -> dict:
    print("--- AGENT: COMPLIANCE JUDGE ---")
    analysis_results = state.get("analysis", [])
    
    failed_requirements = []
    passed_requirements = []
    deferred_requirements = []
    
    for res in analysis_results:
        # Check if the status is NOT_VERIFIABLE or if passed is None
        passed = res.get("passed")
        status = res.get("status")
        
        if status == "NOT_VERIFIABLE" or passed is None:
            deferred_requirements.append({
                "rule": res["requirement"],
                "description": res["description"],
                "reason": res["reason"]
            })
        elif passed is True:
            passed_requirements.append(res["requirement"])
        elif passed is False:
            failed_requirements.append({
                "rule": res["requirement"],
                "description": res["description"],
                "evidence": res.get("evidence", ""),
                "reason": res.get("reason", "")
            })
            
    # Check if any mandatory content requirements failed.
    # Note: platform/performance/profile/submission requirements are DEFERRED/NOT_VERIFIABLE,
    # so they do not fail compliance of the script content itself.
    status = "FAIL" if len(failed_requirements) > 0 else "PASS"
    
    summary = ""
    if status == "PASS":
        summary = "All applicable content compliance requirements passed."
    else:
        summary = f"Violations found: {len(failed_requirements)} requirements failed."
        
    result = {
        "status": status,
        "failed_requirements": failed_requirements,
        "passed_requirements": passed_requirements,
        "deferred_requirements": deferred_requirements,
        "summary": summary
    }
    
    print(f"Compliance Status: {status}")
    if failed_requirements:
        print(f"  Failing rules: {[f['rule'] for f in failed_requirements]}")
    if deferred_requirements:
        print(f"  Deferred rules: {[d['rule'] for d in deferred_requirements]}")
        
    return {"compliance": result}
