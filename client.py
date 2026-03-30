# Copyright (c) 2026 Meta Platforms, Inc. and affiliates.
# MedTriage Environment Client

from openenv.core.mcp_client import MCPToolClient

class MedTriageEnv(MCPToolClient):
    """
    Client for the MedTriage Environment.
    
    Example:
        >>> with MedTriageEnv(base_url="http://localhost:8000") as env:
        ...     obs = env.reset(task_id="TASK_HARD")
        ...     print(obs.symptoms_text)
        ...     result = env.call_tool("triage_patient", level=3, reasoning="High BP and atypical symptoms in elderly patient.")
        ...     print(f"Reward: {result.reward}")
    """
    pass
