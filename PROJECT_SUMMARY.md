# Project Summary: MedTriage OpenEnv
**Meta PyTorch OpenEnv Hackathon Submission**

## 🏥 Project Overview
**MedTriage** is a real-world simulation environment designed for training and evaluating AI agents in clinical decision-making. Unlike "toy" environments, it models a genuine human task: categorizing patient symptoms into appropriate care levels (Self-Care, Clinic, Urgent Care, or Emergency).

## 🛠️ What We Built
We have developed a complete, spec-compliant OpenEnv environment with the following components:

### 1. Core Environment (`server/triage_environment.py`)
- **Action Space**: A `triage_patient` tool where agents assign a triage level (0-3) and provide clinical reasoning.
- **Observation Space**: Detailed patient profiles including demographics, unstructured symptom text, vitals (BP, Temp, HR, SpO2), and medical history.
- **Reward Function**: A medical-safety-first scoring system (0.0 - 1.0) that rewards accuracy and penalizes dangerous under-triage (e.g., missing an emergency).

### 2. Mandatory Tasks
Implemented three specific scenarios with automated graders:
- **TASK_EASY**: Seasonal Allergies (Self-Care)
- **TASK_MEDIUM**: Possible Appendicitis (Urgent Care)
- **TASK_HARD**: Atypical Myocardial Infarction in elderly patient (Emergency)

### 3. API Infrastructure (`server/app.py`)
- Implemented standard OpenEnv endpoints: `/reset`, `/step`, `/state`.
- Added required Hackathon endpoints:
    - `/tasks`: Dynamic list of available scenarios and schemas.
    - `/grader`: Real-time performance scoring.
    - `/baseline`: Automated trigger for the inference script.

### 4. Baseline Inference (`inference.py`)
- Created a reproducible baseline script that leverages the Hackathon's LiteLLM proxy to evaluate the environment. It ensures the environment is "solveable" using a real LLM and serves as a benchmark for API-based agent interactions.

## 🚀 Technical Improvements & Fixes
To ensure the project meets the highest submission standards, we performed the following:
- **Spec Compliance**: Added missing `__init__.py` files and standardized the directory structure to pass `openenv validate`.
- **Dependency Management**: Updated `pyproject.toml` and `server/requirements.txt` to include `openenv-core>=0.2.0` and generated a `uv.lock` file.
- **Containerization**: Optimized the `Dockerfile` to support root-level builds, enabled health checks, and added editable installation (`pip install -e .`) to resolve local module imports.
- **Deployment Automation**: Configured `README.md` with Hugging Face Space metadata (`app_port: 8002`, `sdk: docker`) for seamless hosting.

## 🌐 Deployment Links
- **GitHub Repository**: [https://github.com/ash399/med-triage-openenv](https://github.com/ash399/med-triage-openenv)
- **Hugging Face Space**: [https://huggingface.co/spaces/ashdev/med-triage-openenv](https://huggingface.co/spaces/ashdev/med-triage-openenv)

---
*Documented on: Monday, March 30, 2026*
