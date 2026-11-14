# MLOps AI Agent

This is my Assignment 03 project for MLOps and Production AI Engineering. It puts the common checks an ML engineer does into one small assistant: dataset provenance, experiment comparison, training workflow status, and the health of a deployed API. The tool layer is separate from the chat/orchestration layer, so an answer is based on tool evidence instead of a guess.

The repository starts in demo mode. It uses a checked-in evidence fixture, so it can be tested on any laptop without needing a Kubernetes cluster, MLflow server, DVC remote, or Airflow instance. When real services are available, demo mode can be turned off and the same tool methods use the official clients/APIs.

## What is included

- DVC helpers for datasets, recorded versions, comparisons, change checks, and reproduction.
- MLflow helpers for experiments, runs, metric-based selection, details, and registry data.
- Airflow 3 helpers for DAGs, run status, failed tasks, and a confirmed training trigger.
- Kubernetes helpers for deployments, Pods, Services, logs, and a confirmed restart in one namespace.
- A FastAPI endpoint, CLI, Airflow training DAG, Kubernetes manifests, DVC stage, tests, and GitHub Actions.

## Quick start

I used Python 3.11. Create a virtual environment, install the project, and copy the sample environment file.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
```

The default `DEMO_MODE=true` is intentional. It reads `data/demo_state.json`, which holds the demonstration evidence. To check the assignment workflow from the command line:

```powershell
python -m agent.main "Find the best recent model, identify the dataset version, check deployment status, and explain whether retraining is necessary."
python -m pytest
python -m ruff check .
```

To start the API:

```powershell
uvicorn api.main:app --reload
```

Send a request to `POST /ask`:

```json
{
  "message": "Compare the recent runs and check the Kubernetes deployment"
}
```

For an operation that changes state, confirmation is deliberately separate from the question:

```json
{
  "message": "Trigger the training pipeline",
  "confirmed": true
}
```

## Moving from demo mode to real services

Set `DEMO_MODE=false` in `.env`, install `pip install -e ".[live]"`, and set the URLs/credentials through environment variables. Do not commit `.env` or kubeconfig files.

| Service | What needs to be available | How this project talks to it |
| --- | --- | --- |
| DVC | A repository with DVC initialized and its remote configured | Fixed allowlisted DVC and Git commands |
| MLflow | Tracking URI in `MLFLOW_TRACKING_URI` | `MlflowClient` |
| Airflow | Airflow 3 API URL and an authenticated token | REST calls under `/api/v2` |
| Kubernetes | Local kubeconfig plus the Kubernetes Python package | Official Kubernetes Python client |

The Airflow tool only triggers `ml_training_pipeline`. Kubernetes operations use the `APPROVED_NAMESPACE` value and restart requests require `confirmed=true`. The agent does not start retraining just because a question asks whether retraining is necessary.

## Training workflow and deployment

The training DAG follows `validate_data -> preprocess -> train_model -> evaluate_and_log_mlflow -> quality_gate`. The quality gate fails when F1 is below 0.85, so it blocks any later promotion step. The DVC stage can be run with `dvc repro` once DVC is installed. The Kubernetes files include two replicas, a ClusterIP Service, probes, resource requests/limits, and a ConfigMap. Build the container with `docker build -t mlops-agent:0.1.0 .`; apply manifests only after creating the `mlops-demo` namespace and confirming the image is available to the cluster.

## Tests and evidence

There are 15 automated tests. They cover successful tool calls, tool selection, an invalid dataset, an invalid metric, an unconfirmed Airflow trigger, a non-allowlisted DAG, an unconfirmed Kubernetes restart, an unknown Pod, and a missing MLflow response. The last case is important: the agent reports an uncertainty rather than making up a best model.

`evidence/` contains the exported demo responses used in the report. These are offline demonstration records, not a claim that a live cluster was running on the submission machine. For a live demo, the same questions can be run after setting the service configuration above.

## Project layout

The main folders are `agent/`, `api/`, `dags/`, `training/`, `data/`, `kubernetes/`, `evidence/`, `tests/`, and `report/`.

## Limitations

The repository does not bundle DVC, Airflow, MLflow, or Kubernetes themselves. The demo fixture helps test agent behaviour but does not replace a real deployment. A production version would need role-based Kubernetes access, an Airflow token with a narrow scope, an MLflow backend and artifact store, and monitoring data for a real model-quality decision.
