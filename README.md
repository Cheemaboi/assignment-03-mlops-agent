# MLOps AI Agent

This is my Assignment 03 project for MLOps and Production AI Engineering. It is a small, deterministic assistant for the checks I would normally make separately: which data version was used, which MLflow run is strongest, whether the Airflow training pipeline passed, and whether the deployed API is healthy.

The agent does not use an OpenAI model or an API key. A simple keyword router selects from four approved tools. This makes the behaviour easy to test and stops a chat message from becoming an unrestricted shell command.

## What is in the project

- DVC dataset provenance, version comparison, change checks, and reproduction instructions.
- MLflow queries through `MlflowClient`, including metric-based run selection.
- Authenticated Airflow 3 API calls for DAG status, failures, and an explicitly confirmed training trigger.
- Kubernetes checks through the official Python client for the assignment namespace only.
- A FastAPI endpoint, CLI, Airflow DAG, DVC stage, Kubernetes manifests, local Docker Compose stack, tests, and GitHub Actions.

There are two modes:

- `DEMO_MODE=true` is the default and reads `data/demo_state.json`. It keeps unit tests repeatable without external services.
- `DEMO_MODE=false` uses the real local DVC, MLflow, Airflow, and Kubernetes adapters. I used this mode to produce `evidence/live_local_run.json`.

## Quick start: repeatable demo

Use Python 3.13 (the version used for the live local run) and create a virtual environment.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
python -m agent.main "Find the best recent model, identify the dataset version, check deployment status, and explain whether retraining is necessary."
python -m pytest
python -m ruff check .
```

Start the API with `uvicorn api.main:app --reload`, then send a request to `POST /ask`:

```json
{
  "message": "Compare the recent runs and check the Kubernetes deployment"
}
```

State-changing operations need a separate confirmation:

```json
{
  "message": "Trigger the training pipeline",
  "confirmed": true
}
```

## Local live stack

Docker Desktop needs to be running. The Compose file starts MLflow on port 5000 and Airflow on port 8080.

```powershell
docker compose -f infra/compose.local.yaml up --build -d
```

Airflow Standalone generates a local `admin` password on first start. It is intentionally not committed. Read it from the container, set it only in the current PowerShell session, and use the real adapters:

```powershell
$airflowPassword = (docker compose -f infra/compose.local.yaml exec -T airflow cat /opt/airflow/simple_auth_manager_passwords.json.generated | ConvertFrom-Json).admin
$env:DEMO_MODE = "false"
$env:MLFLOW_TRACKING_URI = "http://localhost:5000"
$env:AIRFLOW_BASE_URL = "http://localhost:8080"
$env:AIRFLOW_USERNAME = "admin"
$env:AIRFLOW_PASSWORD = $airflowPassword
```

Track and reproduce the supplied synthetic dataset with DVC:

```powershell
pip install -e ".[live]"
dvc repro
dvc push
```

`data/raw/customer_churn.csv` is a small deterministic synthetic dataset. Its contents are stored through DVC, while `data/provenance.json` records the readable `v1.0` label used by the training run. The local default DVC remote is `.dvc-storage`, which is intentionally ignored by Git.

For Kubernetes, install `kind` and `kubectl`, then run the commands in `infra/README.md`. The manifests create a two-replica `churn-inference` Deployment, ClusterIP Service, probes, resource limits, and ConfigMap in `mlops-demo`.

## Workflow and guardrails

The Airflow DAG is:

`validate_data -> preprocess -> train_model -> evaluate_and_log_mlflow -> quality_gate`

The quality gate blocks the pipeline when F1 is below 0.85. The DVC stage runs the same logistic-regression training command and writes a reproducible metrics file. The agent does not automatically retrain a model: it needs a freshness-policy breach, failed quality gate, or a degradation signal.

The tool boundaries are intentional. DVC uses fixed argument lists, the Airflow trigger is allowlisted to `ml_training_pipeline`, Kubernetes reads are scoped to `APPROVED_NAMESPACE`, and both DAG triggering and deployment restart require `confirmed=true`. Secrets belong in environment variables, never in the repository.

## Verification evidence

The live local verification produced:

- DVC dataset `customer_churn` version `v1.0`, with a clean `dvc status --json` result.
- A best MLflow logistic-regression run with F1 `0.9787` and accuracy `0.9833`.
- A successful Airflow run where all five tasks completed.
- Kubernetes `churn-inference` at `2/2` ready replicas behind a ClusterIP Service.

The full exported summary is in `evidence/live_local_run.json`. The older files in `evidence/` are clearly labelled offline fixture evidence used by unit tests; they are not presented as live output.

## Project layout

The main folders are `agent/`, `api/`, `dags/`, `training/`, `data/`, `infra/`, `kubernetes/`, `evidence/`, `tests/`, and `report/`.
