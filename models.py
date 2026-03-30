# Copyright (c) 2026 Meta Platforms, Inc. and affiliates.
# MedTriage Environment - Type-Safe Models

from typing import Dict, List, Optional, Any
from enum import IntEnum
from pydantic import BaseModel, Field

# Core Triage Levels
class TriageLevel(IntEnum):
    SELF_CARE = 0      # Over-the-counter/rest
    CLINIC = 1         # Primary Care appointment (next 24-48h)
    URGENT_CARE = 2    # Same-day clinic (e.g., potential fracture)
    EMERGENCY = 3      # Immediate ER/Ambulance (life-threatening)

# 1. Action Model
class TriageAction(BaseModel):
    level: TriageLevel = Field(..., description="Recommended triage level (0-3)")
    reasoning: str = Field(..., description="Medical justification for the triage level")
    follow_up_questions: List[str] = Field(default_factory=list, description="Questions to ask the patient if more info is needed")

# 2. Observation Model
class TriageObservation(BaseModel):
    patient_id: str
    age: int
    gender: str
    symptoms_text: str = Field(..., description="Unstructured description of symptoms from patient")
    vitals: Dict[str, Any] = Field(default_factory=dict, description="Vitals like temp, bp, hr, spo2")
    history: List[str] = Field(default_factory=list, description="Relevant past conditions or medications")
    done: bool = False
    reward: float = 0.0
    message: str = ""

# 3. State Model (Metadata)
class TriageState(BaseModel):
    episode_id: str
    step_count: int = 0
    current_task_id: str = ""
    ground_truth_level: TriageLevel = TriageLevel.SELF_CARE
