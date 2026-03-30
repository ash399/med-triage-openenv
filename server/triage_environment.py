# Copyright (c) 2026 Meta Platforms, Inc. and affiliates.
# MedTriage Environment Implementation

import uuid
from typing import Any, Dict, Optional
from uuid import uuid4

# Imports (Adjust according to actual structure)
from openenv.core.env_server.mcp_environment import MCPEnvironment
from openenv.core.env_server.types import Action, Observation, State
from fastmcp import FastMCP

# Use local models
try:
    from .models import TriageLevel, TriageAction, TriageObservation, TriageState
except ImportError:
    from models import TriageLevel, TriageAction, TriageObservation, TriageState

# Task Scenarios (Easy -> Medium -> Hard)
TASKS = {
    "TASK_EASY": {
        "id": "TASK_EASY",
        "name": "Seasonal Allergies",
        "patient": {
            "patient_id": "P-101", "age": 28, "gender": "Female",
            "symptoms_text": "I've had a runny nose, sneezing, and itchy eyes for the past week. It's really annoying but I don't feel 'sick' otherwise.",
            "vitals": {"temp": 98.6, "bp": "120/80", "hr": 72, "spo2": 99},
            "history": ["No major conditions"]
        },
        "ground_truth": TriageLevel.SELF_CARE
    },
    "TASK_MEDIUM": {
        "id": "TASK_MEDIUM",
        "name": "Possible Appendicitis",
        "patient": {
            "patient_id": "P-102", "age": 19, "gender": "Male",
            "symptoms_text": "I woke up with severe pain around my belly button that's moving down to my lower right side. I feel nauseous and have zero appetite.",
            "vitals": {"temp": 100.8, "bp": "115/75", "hr": 95, "spo2": 98},
            "history": ["No major conditions"]
        },
        "ground_truth": TriageLevel.URGENT_CARE
    },
    "TASK_HARD": {
        "id": "TASK_HARD",
        "name": "Atypical Myocardial Infarction",
        "patient": {
            "patient_id": "P-103", "age": 68, "gender": "Female",
            "symptoms_text": "I just feel extremely weak and have this weird 'indigestion' sensation in my upper stomach. I'm also sweating a lot for no reason.",
            "vitals": {"temp": 98.2, "bp": "165/100", "hr": 105, "spo2": 94},
            "history": ["Type 2 Diabetes", "High Blood Pressure", "Smoking"]
        },
        "ground_truth": TriageLevel.EMERGENCY
    }
}

class MedTriageEnvironment(MCPEnvironment):
    """
    Real-world Triage Environment for Agent Training.
    """

    def __init__(self):
        mcp = FastMCP("med_triage_env")

        @mcp.tool
        def triage_patient(level: int, reasoning: str) -> str:
            """
            Analyze patient data and assign a triage level (0-3).
            
            Args:
                level: 0 (Self-Care), 1 (Clinic), 2 (Urgent Care), 3 (Emergency)
                reasoning: Medical explanation for your decision
            """
            return f"Triage decision received: Level {level}. Reason: {reasoning}"

        super().__init__(mcp)
        self._state = TriageState(episode_id=str(uuid4()))
        self._current_task = None

    def reset(self, task_id: Optional[str] = "TASK_EASY", **kwargs: Any) -> TriageObservation:
        """Reset the environment with a specific task (EASY, MEDIUM, or HARD)."""
        task_id = task_id or "TASK_EASY"
        if task_id not in TASKS:
            task_id = "TASK_EASY"
            
        self._current_task = TASKS[task_id]
        self._state = TriageState(
            episode_id=str(uuid4()),
            step_count=0,
            current_task_id=task_id,
            ground_truth_level=self._current_task["ground_truth"]
        )

        patient = self._current_task["patient"]
        return TriageObservation(
            patient_id=patient["patient_id"],
            age=patient["age"],
            gender=patient["gender"],
            symptoms_text=patient["symptoms_text"],
            vitals=patient["vitals"],
            history=patient["history"],
            message=f"New Patient Triage: {self._current_task['name']}"
        )

    def _calculate_reward(self, agent_level: TriageLevel, ground_truth: TriageLevel) -> float:
        """
        Scoring Logic (0.0 - 1.0):
        - Perfect Match: 1.0
        - Over-triage (too safe): 0.5 (safe but resource heavy)
        - Minor Under-triage: 0.2 (delay in care)
        - Major Under-triage (dangerous): 0.0 (unsafe)
        """
        if agent_level == ground_truth:
            return 1.0
        
        # Dangerously Under-triaging an Emergency
        if ground_truth == TriageLevel.EMERGENCY and agent_level < TriageLevel.URGENT_CARE:
            return 0.0
            
        # Over-triaging is better than under-triaging in medicine
        if agent_level > ground_truth:
            return 0.5
            
        return 0.2

    def step(self, action: Action, **kwargs: Any) -> TriageObservation:
        """
        Process the agent's triage decision and return a score.
        """
        self._state.step_count += 1
        
        # If the action is an MCP CallToolAction (from step())
        from openenv.core.env_server.mcp_types import CallToolAction
        
        if isinstance(action, CallToolAction) and action.tool_name == "triage_patient":
            agent_level = action.arguments.get("level")
            reward = self._calculate_reward(TriageLevel(agent_level), self._state.ground_truth_level)
            self._last_reward = reward
            
            patient = self._current_task["patient"]
            return TriageObservation(
                **patient,
                done=True,
                reward=reward,
                message=f"Episode complete. Agent Triage: {agent_level}. Ground Truth: {self._state.ground_truth_level.value}. Score: {reward}"
            )

        # Handle non-MCP fallback or invalid actions
        obs = super().step(action, **kwargs)
        return obs

    @property
    def state(self) -> State:
        return self._state
