# app/agents/quality.py
"""
Content Quality Agent (Agent 5).

Evaluates script quality dimensions relative to campaign context in a single Qwen call.
Scored 0-10.
"""
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from app.llm.provider import get_quality_llm
from app.state import ContentState

class QualityScoreResponse(BaseModel):
    hook: int = Field(description="Score from 0-10 for the video hook (attention grabbing)")
    clarity: int = Field(description="Score from 0-10 for clarity of message")
    campaign_relevance: int = Field(description="Score from 0-10 for relevance to campaign requirements")
    curiosity: int = Field(description="Score from 0-10 for creating curiosity about Jeremy and Whop")
    original_content_pull: int = Field(description="Score from 0-10 for drawing in original podcast/doc content style/pull")
    cta_quality: int = Field(description="Score from 0-10 for how compelling the Call to Action is")
    naturalness: int = Field(description="Score from 0-10 for conversational/natural flow")
    confidence: float = Field(description="Self-confidence in evaluation from 0.0 to 1.0")
    weaknesses: list[str] = Field(description="List of specific quality weaknesses or areas to improve")

def quality_agent(state: ContentState) -> dict:
    print("--- AGENT: CONTENT QUALITY EVALUATOR ---")
    
    content = state["content"]
    raw_reqs = state.get("raw_requirements", "")
    
    llm = get_quality_llm(temperature=0.2)
    structured_llm = llm.with_structured_output(QualityScoreResponse)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are a professional content quality reviewer.\n"
         "Evaluate the provided video script against the campaign context.\n"
         "Score each of the following dimensions from 0 to 10:\n"
         "- hook: does it grab attention in the first 2 seconds?\n"
         "- clarity: is the value proposition clear?\n"
         "- campaign_relevance: does it align with the spirit of the campaign?\n"
         "- curiosity: does it generate interest in Jeremy's methods/Whop without giving everything away?\n"
         "- original_content_pull: does it feel like an authentic snippet/clip pulling from a larger podcast/documentary?\n"
         "- cta_quality: is the call to action clear and enticing?\n"
         "- naturalness: does it sound conversational and not like a reading list?\n\n"
         "Be critical and realistic. Scores >= 8 must represent excellent, viral-ready content."),
        ("human", 
         "CAMPAIGN CONTEXT:\n{raw_reqs}\n\n"
         "SCRIPT CONTENT:\n{content}")
    ])
    
    chain = prompt | structured_llm
    
    print("Evaluating content quality with Qwen 14B...")
    scores = chain.invoke({"raw_reqs": raw_reqs, "content": content})
    
    # Calculate simple average
    scores_dict = scores.model_dump()
    dimensions = [
        "hook", "clarity", "campaign_relevance", "curiosity", 
        "original_content_pull", "cta_quality", "naturalness"
    ]
    total = sum(scores_dict[d] for d in dimensions)
    overall_score = round(total / len(dimensions), 2)
    
    scores_dict["overall_score"] = overall_score
    
    print(f"Overall Quality Score: {overall_score}/10")
    print(f"Scores: Hook={scores.hook}, Curiosity={scores.curiosity}, CTA={scores.cta_quality}")
    print(f"Weaknesses: {scores.weaknesses}")
    
    return {"quality": scores_dict}
