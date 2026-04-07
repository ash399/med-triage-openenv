# Copyright (c) 2026 Meta Platforms, Inc. and affiliates.
# MedTriage - Baseline Inference Script

import os
import time
import json
import requests
import asyncio
from typing import List, Dict, Any
from client import MedTriageEnv

# --- Mandatory Environment Configuration ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8002/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "med-triage-baseline")
HF_TOKEN = os.getenv("HF_TOKEN", "dummy-token")

# --- Structured Logging Functions ---
def log_start(task: str, env: str, model: str):
    """Emit structured [START] log."""
    data = {
        "timestamp": time.time(),
        "task": task,
        "env": env,
        "model": model,
        "config": {
            "api_base": API_BASE_URL,
            "max_steps": 10
        }
    }
    print(f"[START] {json.dumps(data)}", flush=True)

def log_step(step: int, action: Any, reward: float, done: bool, error: str = None):
    """Emit structured [STEP] log."""
    data = {
        "timestamp": time.time(),
        "step": step,
        "action": action,
        "reward": reward,
        "done": done,
        "error": error
    }
    print(f"[STEP] {json.dumps(data)}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    """Emit structured [END] log."""
    data = {
        "timestamp": time.time(),
        "success": success,
        "steps_taken": steps,
        "score": score,
        "rewards": rewards
    }
    print(f"[END] {json.dumps(data)}", flush=True)

# --- Server Readiness Check ---
def wait_for_server(url: str, timeout: int = 30):
    """Wait for the server to be ready before proceeding."""
    start_time = time.time()
    health_url = f"{url.rstrip('/')}/health"
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(health_url, timeout=2)
            if response.status_code == 200:
                return True
        except (requests.RequestException, ConnectionError):
            pass
        time.sleep(1)
    return False

def run_baseline(base_url: str = "http://localhost:8002"):
    """Run baseline agent against all 3 tasks and return results."""
    # Ensure base_url uses the port from environment if available
    env_port = os.environ.get("PORT", "8002")
    if "localhost" in base_url and f":{env_port}" not in base_url:
        base_url = f"http://localhost:{env_port}"

    # Wait for server readiness
    wait_for_server(base_url)

    tasks = ["TASK_EASY", "TASK_MEDIUM", "TASK_HARD"]
    all_scores = {}
    
    try:
        from client import MedTriageEnv
    except ImportError:
        from .client import MedTriageEnv

    for task_id in tasks:
        log_start(task=task_id, env="med_triage_env", model=MODEL_NAME)
        
        rewards = []
        steps_taken = 0
        success = False
        final_score = 0.0
        
        try:
            with MedTriageEnv(base_url=base_url).sync() as env:
                obs = env.reset(task_id=task_id)
                steps_taken = 1
                
                # Heuristic Logic (mimes model output)
                bp_sys = int(obs.vitals.get("bp", "120/80").split("/")[0])
                if bp_sys > 150 or obs.age > 65:
                    level = 3 # EMERGENCY
                elif "severe pain" in obs.symptoms_text.lower():
                    level = 2 # URGENT_CARE
                else:
                    level = 0 # SELF_CARE
                
                action = {"tool_name": "triage_patient", "arguments": {"level": level, "reasoning": "Heuristic baseline."}}
                result = env.step(action)
                
                reward = result.reward or 0.0
                done = result.done
                rewards.append(reward)
                
                log_step(step=1, action=action, reward=reward, done=done)
                
                final_score = reward
                success = reward >= 1.0
                all_scores[task_id] = reward
                
        except Exception as e:
            log_step(step=steps_taken, action=None, reward=0.0, done=True, error=str(e))
            all_scores[task_id] = 0.0
            
        log_end(success=success, steps=steps_taken, score=final_score, rewards=rewards)
            
    return all_scores

if __name__ == "__main__":
    try:
        results = run_baseline()
        # Final summary for human readability
        print(f"\n📊 FINAL BASELINE SCORES: {results}")
    except Exception as e:
        print(f"FATAL: {e}")
        import sys
        sys.exit(1)
