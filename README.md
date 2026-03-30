---
title: MedTriage OpenEnv
emoji: 🏥
sdk: docker
pinned: false
app_port: 7860
tags:
  - openenv
  - healthcare
  - ai-agents
---

# MedTriage OpenEnv

A real-world medical triage simulation environment built for the Meta PyTorch OpenEnv Hackathon. This environment allows AI agents to learn how to categorize patient symptoms into appropriate clinical triage levels using the standard OpenEnv API.

## 📋 Environment Overview

**MedTriage** simulates the decision-making process of a clinical triage officer. The agent receives patient demographics, vitals, and unstructured symptom text, and must decide on the safest and most efficient path for care.

### 🎯 Real-World Utility
In real healthcare settings, accurate triage is critical for:
1. **Patient Safety**: Ensuring life-threatening conditions (like heart attacks) are seen immediately.
2. **Resource Optimization**: Preventing hospital ERs from being overwhelmed by minor cases that can be treated at home.

---

## 🎮 Action Space

The agent interacts via the `triage_patient` tool:

- **level**: (IntEnum)
  - `0`: **Self-Care** (Over-the-counter/rest)
  - `1`: **Clinic** (Primary Care appointment in 24-48h)
  - `2`: **Urgent Care** (Same-day care)
  - `3`: **Emergency** (Immediate ER/Ambulance)
- **reasoning**: (String) A medical justification for the triage level.

---

## 📥 Observation Space

Each observation provides:
- **patient_id**: Unique identifier.
- **age / gender**: Basic demographics.
- **symptoms_text**: Unstructured description of the patient's complaint.
- **vitals**: Dictionary containing `temp`, `bp` (Blood Pressure), `hr` (Heart Rate), and `spo2` (Oxygen).
- **history**: List of prior medical conditions or medications.

---

## 🚀 Tasks & Difficulty

The environment includes 3 built-in tasks with automated graders:

| Task ID | Name | Difficulty | Ground Truth |
|---------|------|------------|--------------|
| `TASK_EASY` | Seasonal Allergies | Easy | Self-Care (0) |
| `TASK_MEDIUM` | Possible Appendicitis | Medium | Urgent Care (2) |
| `TASK_HARD` | Atypical MI | Hard | Emergency (3) |

---

## 📈 Reward Function (Grader)

Scores range from **0.0 to 1.0**:
- **1.0**: Perfect match with ground truth.
- **0.5**: Over-triage (Safe but resource-intensive).
- **0.2**: Minor under-triage.
- **0.0**: Dangerous under-triage (e.g., sending a heart attack to self-care).

---

## 🛠️ Setup & Usage

### Local Development
1. **Install Dependencies**:
   ```bash
   pip install -e .
   ```
2. **Start the Server**:
   ```bash
   python server/app.py
   ```
3. **Run Baseline**:
   ```bash
   python inference.py
   ```

### Docker
```bash
docker build -t med-triage-env:latest .
docker run -p 8002:8002 med-triage-env:latest
```

---

## 🌐 API Endpoints
- `/tasks`: List all available tasks.
- `/baseline`: Run the baseline inference.
- `/grader`: Get the score of the last episode.
- `/health`: Environment health check.
