# app/api.py
"""
FastAPI Server for Campaign-Aware Content Evaluator & Optimizer UI.

Exposes REST endpoints to trigger multi-agent evaluation and serves the web frontend.
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

from app.graph import build_workflow

app = FastAPI(
    title="Campaign-Aware Content Evaluator API",
    description="Multi-Agent Content Evaluation and Optimization System",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EvaluationRequest(BaseModel):
    campaign_text: str = Field(description="Raw campaign rules and requirements text")
    script_text: str = Field(description="Draft script/content text to evaluate")
    use_fast_model: Optional[bool] = Field(default=True, description="If True, uses fast llama3.2:1b for all steps")


@app.post("/api/evaluate")
async def evaluate_content(request: EvaluationRequest):
    """
    Triggers the full multi-agent LangGraph workflow:
    Requirement Extraction -> Feasibility -> Analysis -> Compliance -> Quality -> Improvement
    """
    if not request.campaign_text.strip():
        raise HTTPException(status_code=400, detail="Campaign requirements text cannot be empty.")
    if not request.script_text.strip():
        raise HTTPException(status_code=400, detail="Script text cannot be empty.")

    # Configure model strategy via env variable
    if request.use_fast_model:
        os.environ["QUALITY_MODEL"] = "llama3.2:1b"
    else:
        os.environ["QUALITY_MODEL"] = "qwen3:14b"

    initial_state = {
        "original_content": request.script_text,
        "content": request.script_text,
        "raw_requirements": request.campaign_text,
        "requirements": [],
        "revision_count": 0,
        "revision_history": []
    }

    try:
        workflow = build_workflow()
        final_state = workflow.invoke(initial_state)
        return {
            "success": True,
            "decision": final_state.get("decision"),
            "requirements": final_state.get("requirements", []),
            "feasibility": final_state.get("feasibility", {}),
            "analysis": final_state.get("analysis", []),
            "compliance": final_state.get("compliance", {}),
            "quality": final_state.get("quality", {}),
            "revision_count": final_state.get("revision_count", 0),
            "revision_history": final_state.get("revision_history", []),
            "final_content": final_state.get("content", ""),
            "original_content": final_state.get("original_content", "")
        }
    except Exception as e:
        print(f"Workflow execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/samples")
async def get_sample_data():
    """Returns default sample campaign and content text for quick UI testing."""
    campaign_path = "data/campaign.txt"
    content_path = "data/content.txt"

    campaign_text = ""
    script_text = ""

    if os.path.exists(campaign_path):
        with open(campaign_path, "r", encoding="utf-8") as f:
            campaign_text = f.read()

    if os.path.exists(content_path):
        with open(content_path, "r", encoding="utf-8") as f:
            script_text = f.read()

    return {
        "campaign_text": campaign_text,
        "script_text": script_text
    }


# Mount static directory for frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
