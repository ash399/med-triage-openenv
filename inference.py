# Copyright (c) 2026 Meta Platforms, Inc. and affiliates.
# MedTriage - Baseline Inference Script

import os
import time
import subprocess
import requests
from client import MedTriageEnv

def run_baseline(base_url: str = "http://localhost:8002"):
    """Run baseline agent against all 3 tasks and return results."""
    print(f"🚀 Starting MedTriage Baseline Inference on {base_url}...")
    
    tasks = ["TASK_EASY", "TASK_MEDIUM", "TASK_HARD"]
    scores = {}
    
    # Simple heuristic-based baseline (no LLM required for this local test)
    try:
        from client import MedTriageEnv
    except ImportError:
        from .client import MedTriageEnv

    with MedTriageEnv(base_url=base_url).sync() as env:
        for task_id in tasks:
            print(f"📋 Running {task_id}...", end=" ", flush=True)
            obs = env.reset(task_id=task_id)
            
            # Simple heuristic logic
            bp_sys = int(obs.vitals.get("bp", "120/80").split("/")[0])
            
            if bp_sys > 150 or obs.age > 65:
                level = 3 # EMERGENCY
            elif "severe pain" in obs.symptoms_text.lower():
                level = 2 # URGENT_CARE
            else:
                level = 0 # SELF_CARE
                
            result = env.step({"tool_name": "triage_patient", "arguments": {"level": level, "reasoning": "Heuristic baseline."}})
            scores[task_id] = result.reward
            print(f"Score: {result.reward}")
            
    return scores

if __name__ == "__main__":
    results = run_baseline()
    print("\n📊 FINAL BASELINE SCORES:", results)
