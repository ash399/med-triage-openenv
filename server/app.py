# Copyright (c) 2026 Meta Platforms, Inc. and affiliates.
# FastAPI application for MedTriage Environment

from fastapi import FastAPI, Request
from openenv.core.env_server.http_server import create_app
from openenv.core.env_server.mcp_types import CallToolAction, CallToolObservation
from pydantic import BaseModel
from typing import List, Dict, Any

try:
    from server.triage_environment import MedTriageEnvironment, TASKS
    from models import TriageAction
except ImportError:
    try:
        from .triage_environment import MedTriageEnvironment, TASKS
        from .models import TriageAction
    except ImportError:
        from triage_environment import MedTriageEnvironment, TASKS
        from models import TriageAction

# Initialize the environment instance to be used by the app
env_instance = MedTriageEnvironment()

# Create the base OpenEnv app
app = create_app(
    MedTriageEnvironment, 
    CallToolAction, 
    CallToolObservation, 
    env_name="med_triage_env"
)

# --- Additional Hackathon Endpoints ---

@app.get("/tasks")
async def get_tasks():
    """Returns list of tasks and the action schema."""
    task_list = []
    for tid, tdata in TASKS.items():
        task_list.append({
            "id": tid,
            "name": tdata["name"],
            "difficulty": tid.split("_")[1].lower()
        })
    
    return {
        "tasks": task_list,
        "action_schema": TriageAction.model_json_schema()
    }

@app.get("/grader")
async def get_grader():
    """Returns the most recent grader score."""
    state = env_instance.state
    # In a real multi-session env, we'd lookup by session_id
    # For a simple demo, we return the last calculated reward if available
    return {"score": getattr(env_instance, "_last_reward", 0.0)}

@app.get("/baseline")
async def trigger_baseline():
    """
    Trigger baseline inference script and return scores.
    """
    try:
        from ..inference import run_baseline
    except ImportError:
        import sys
        import os
        # Add parent dir to sys.path if not there
        parent_dir = os.path.dirname(os.path.dirname(__file__))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
        from inference import run_baseline
    
    # Get current port from environment or default to 8002
    port = os.environ.get("PORT", "8002")
    
    # Execute actual baseline
    scores = run_baseline(base_url=f"http://localhost:{port}")
    
    return {
        "status": "baseline_completed",
        "baseline_scores": scores
    }

def main():
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
