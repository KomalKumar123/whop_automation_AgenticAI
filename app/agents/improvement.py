# app/agents/improvement.py
"""
Improvement Agent (Agent 6).

Uses Qwen 14B to revise the script to:
1. Fix failed compliance requirements.
2. Improve low-scoring quality dimensions (especially those in quality weaknesses).
3. Preserve passing requirements.
"""
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from app.llm.provider import get_quality_llm
from app.state import ContentState

class ImprovedContentResponse(BaseModel):
    updated_content: str = Field(description="The fully revised and rewritten script content")
    changes_made: list[str] = Field(description="List of specific changes made to address compliance or quality issues")

def improvement_agent(state: ContentState) -> dict:
    print("--- AGENT: CONTENT IMPROVER ---")
    
    content = state["content"]
    raw_reqs = state.get("raw_requirements", "")
    
    # Extract failed requirements
    compliance = state.get("compliance", {})
    failed_reqs = compliance.get("failed_requirements", [])
    failed_reqs_text = "\n".join(
        f"- {f['rule']}: {f['description']} (Evidence: {f.get('evidence', '')})" 
        for f in failed_reqs
    ) if failed_reqs else "None"
    
    # Extract quality weaknesses
    quality = state.get("quality", {})
    weaknesses = quality.get("weaknesses", [])
    weaknesses_text = "\n".join(f"- {w}" for w in weaknesses) if weaknesses else "None"
    quality_scores = ", ".join(f"{k}: {v}/10" for k, v in quality.items() if k not in ["weaknesses", "confidence", "overall_score"])
    
    llm = get_quality_llm(temperature=0.6)
    structured_llm = llm.with_structured_output(ImprovedContentResponse)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are an expert script writer and content optimizer.\n"
         "Your task is to rewrite the video script to satisfy all campaign requirements and maximize quality.\n\n"
         "CRITICAL RULES:\n"
         "1. Fix every failed compliance requirement listed.\n"
         "2. Address the quality weaknesses listed, keeping overall flow natural.\n"
         "3. Preserve the elements of the script that already passed.\n"
         "4. Do NOT add hashtags or tag mentions unless explicitly requested in the requirements.\n"
         "5. Do NOT make unrealistic or unsupported claims. Keep it clean and organic.\n"
         "6. Make sure the output contains ONLY the revised script in the 'updated_content' field."),
        ("human",
         "CAMPAIGN REQUIREMENTS:\n{raw_reqs}\n\n"
         "CURRENT SCRIPT:\n{content}\n\n"
         "FAILED COMPLIANCE REQUIREMENTS:\n{failed_reqs}\n\n"
         "CURRENT QUALITY SCORES:\n{quality_scores}\n"
         "QUALITY WEAKNESSES:\n{weaknesses}")
    ])
    
    chain = prompt | structured_llm
    
    print("Revising script with Qwen 14B...")
    result = chain.invoke({
        "raw_reqs": raw_reqs,
        "content": content,
        "failed_reqs": failed_reqs_text,
        "quality_scores": quality_scores,
        "weaknesses": weaknesses_text
    })
    
    # Record revision history
    history_entry = {
        "revision": state.get("revision_count", 0) + 1,
        "previous_content": content,
        "updated_content": result.updated_content,
        "changes_made": result.changes_made,
        "quality_before": quality.get("overall_score", 0.0)
    }
    
    print(f"Revision {history_entry['revision']} completed.")
    print(f"Changes: {result.changes_made}")
    
    # Return updated content, incremented revision count, and appended history
    history = state.get("revision_history", []).copy()
    history.append(history_entry)
    
    return {
        "content": result.updated_content,
        "revision_count": state.get("revision_count", 0) + 1,
        "revision_history": history
    }
