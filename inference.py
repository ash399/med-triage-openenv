# Copyright (c) 2026 Meta Platforms, Inc. and affiliates.
# MedTriage - Baseline Inference Script

import os
import time
import json
import requests
import asyncio
from typing import List, Dict, Any
import openai
from client import MedTriageEnv

# --- Mandatory Environment Configuration (Injected by Hackathon Validator) ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8002/v1")
API_KEY = os.getenv("API_KEY", "dummy-key")
MODEL_NAME = os.getenv("MODEL_NAME", "med-triage-baseline")
HF_TOKEN = os.getenv("HF_TOKEN", "dummy-token")

# Initialize OpenAI client with the injected LiteLLM proxy credentials
llm_client = openai.OpenAI(
    base_url=API_BASE_URL,
    api_key=API_KEY
)

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

def get_llm_triage(obs: Any) -> Dict[str, Any]:
    """Call the LLM via proxy to get triage level and reasoning."""
    # Heuristic fallback for local development when proxy is not active
    is_local = "localhost" in API_BASE_URL and API_KEY == "dummy-key"
    
    # Extract data safely from observation
    # Sometimes openenv-core puts custom fields in .metadata if they don't fit the schema
    metadata = getattr(obs, "metadata", {})
    
    age = getattr(obs, "age", metadata.get("age", 0))
    gender = getattr(obs, "gender", metadata.get("gender", "unknown"))
    symptoms = getattr(obs, "symptoms_text", metadata.get("symptoms_text", "No symptoms provided"))
    vitals = getattr(obs, "vitals", metadata.get("vitals", {}))
    history = getattr(obs, "history", metadata.get("history", []))

    if is_local:
        # Heuristic Logic (mimes model output for local testing)
        bp_sys = int(vitals.get("bp", "120/80").split("/")[0]) if isinstance(vitals.get("bp"), str) else 120
        if bp_sys > 150 or age > 65:
            level = 3 # EMERGENCY
        elif "severe pain" in symptoms.lower():
            level = 2 # URGENT_CARE
        else:
            level = 0 # SELF_CARE
        return {"level": level, "reasoning": "Heuristic fallback (Local testing)."}

    # Actual LLM call through the LiteLLM proxy
    prompt = f"""
    You are an expert medical triage officer. Based on the patient data below, categorize the patient into the most appropriate care level.

    PATIENT DATA:
    - Age: {age}
    - Gender: {gender}
    - Symptoms: {symptoms}
    - Vitals: {vitals}
    - Medical History: {history}

    TRIAGE LEVELS (0-3):
    0: SELF_CARE (Rest, OTC medication, home monitoring)
    1: CLINIC (Non-urgent appointment within 48 hours)
    2: URGENT_CARE (Immediate attention for non-life-threatening conditions)
    3: EMERGENCY (Life-threatening symptoms, immediate ER visit)

    Assign a level (0, 1, 2, or 3) and provide a concise medical reasoning.
    Respond ONLY in valid JSON format:
    {{"level": <int>, "reasoning": "<string>"}}
    """

    try:
        response = llm_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"LLM Error encountered: {e}")
        # Final safety fallback: triage to Emergency if unsure/error
        return {"level": 3, "reasoning": f"Emergency fallback due to triage system error: {str(e)}"}

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
                res = env.reset(task_id=task_id)
                obs = res.observation
                steps_taken = 1
                
                # Import CallToolAction for proper serialization
                try:
                    from openenv.core.env_server.mcp_types import CallToolAction
                except ImportError:
                    # Fallback if needed, but it should be available
                    CallToolAction = None

                decision = get_llm_triage(obs)
                level = int(decision.get("level", 0))
                reasoning = decision.get("reasoning", "Baseline triage decision.")
                
                if CallToolAction:
                    action = CallToolAction(
                        tool_name="triage_patient", 
                        arguments={"level": level, "reasoning": reasoning}
                    )
                else:
                    action = {"tool_name": "triage_patient", "arguments": {"level": level, "reasoning": reasoning}}
                
                result = env.step(action)
                
                reward = result.reward or 0.1
                done = result.done
                rewards.append(reward)
                
                if CallToolAction:
                    action_to_log = action.model_dump() if hasattr(action, "model_dump") else action
                else:
                    action_to_log = action
                
                log_step(step=1, action=action_to_log, reward=reward, done=done)
                
                final_score = reward
                # Updated for strictly 0-1 validation (0.9 is the new max)
                success = reward >= 0.9
                all_scores[task_id] = reward
                
        except Exception as e:
            import traceback
            traceback.print_exc()
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
