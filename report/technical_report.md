# Technical Report — MLOps AI Agent

## 1. What I built

For this assignment, I built a small MLOps assistant around four real operations: DVC data provenance, MLflow experiment tracking, an Airflow training workflow, and Kubernetes application checks. I kept the agent deterministic on purpose. It routes a request to approved tools instead of relying on an LLM to invent an answer, so every operational statement can be traced back to a tool response.

There is no OpenAI dependency or API key in this project. The offline fixture mode supports repeatable tests, while the same adapters can be switched to local live services with `DEMO_MODE=false`.

## 2. Design

The command-line program and FastAPI `/ask` endpoint call the same orchestrator. Each tool returns a `ToolResult` containing its name, success state, data, evidence source, duration, and an error when something goes wrong. This made it possible to return partial results honestly instead of filling in a missing fact.

The DVC adapter uses fixed DVC and Git commands. The MLflow adapter uses `MlflowClient`, not browser scraping. The Airflow adapter exchanges local credentials for a short-lived bearer token and calls the Airflow 3 REST API. The Kubernetes adapter uses the official Python client and is scoped to the approved `mlops-demo` namespace.

The workflow is `validate_data -> preprocess -> train_model -> evaluate_and_log_mlflow -> quality_gate`. Validation checks the CSV schema and class labels. Training logs its parameters, metrics, source-data label, and Git revision to MLflow. The final gate raises an error below F1 0.85, so training does not silently become promotion.

## 3. Safety choices

The project never executes a command copied from a question. Airflow can only trigger `ml_training_pipeline`; Kubernetes restart and Airflow trigger requests need `confirmed=true`; and the structured logger removes values whose key looks like a token or secret. The agent recommends review before promotion and does not start retraining merely because a user asks it to.

## 4. Live local evidence

I ran the local services with Docker Desktop, a kind Kubernetes cluster, and the DVC repository in this project. The exported result is stored in `evidence/live_local_run.json`.

| Area | Live result | What it shows |
| --- | --- | --- |
| DVC | `customer_churn`, version `v1.0`; clean `dvc status --json` | The synthetic CSV is DVC-tracked and the training stage is reproducible. |
| MLflow | logistic regression, F1 `0.9787`, accuracy `0.9833` | The best completed run was selected through `MlflowClient`. |
| Airflow | `manual__2026-11-14T22:52:44.199604+00:00`, `success` | Validation, preprocessing, training, MLflow logging, and the quality gate all completed. |
| Kubernetes | `churn-inference`, `2/2` ready | The inference service was running behind a ClusterIP Service. |

The earlier JSON files in `evidence/` are offline fixtures for tests. They are not used as proof of the local run above.

## 5. Five checks I tried

1. **Which dataset version was used?** The DVC tool returned `v1.0`, the pointer file `data/raw/customer_churn.csv.dvc`, and the current Git revision. It also gives the reproduction command for the version label.
2. **Which run is strongest?** MLflow selected the logistic-regression run with F1 0.9787. The answer still recommends validation, fairness, latency, and approval checks before production promotion.
3. **Did the pipeline finish?** Airflow returned a successful manual run with all five task instances in `success`.
4. **Is the prediction API available?** The Kubernetes tool returned two ready replicas for `churn-inference`; the ClusterIP Service exposes port 80 to the application port.
5. **What is the overall MLOps status?** In one request the agent used MLflow, DVC, Kubernetes, and Airflow. It found a healthy deployment and successful pipeline, but correctly did not recommend automatic retraining because there was no degradation or policy failure.

## 6. Two failures and how I resolved them

The first live Airflow attempt could not find the DVC-materialized CSV because the container had been started before the data file was restored. I recreated only the Airflow container after DVC materialization and verified that `/opt/airflow/data/raw/customer_churn.csv` was present. The next run passed validation.

The second issue was MLflow's host-header allow-list. Local clients used `localhost:5000` and the Airflow container used `mlflow:5000`; both include a port. I added those exact local hosts to the Compose configuration, recreated MLflow, and verified a training run through both paths. A separate parsing issue then appeared because MLflow prints a run URL before the JSON summary. The DAG now reads the final non-empty output line, which is the script's structured summary.

The automated tests also cover an unconfirmed Airflow trigger, a non-allowlisted DAG, an unconfirmed Kubernetes restart, an unknown Pod, an invalid dataset, an invalid metric, and an unavailable MLflow response. In each case the agent reports the failure rather than inventing a success.

## 7. Testing and limits

The GitHub Actions workflow runs Ruff and pytest. The local stack is meant for a coursework demonstration, not a production deployment: Airflow Standalone is local-only, the DVC remote is a local folder, and MLflow uses SQLite. A production version would use role-based service accounts, managed artifact storage, monitoring for latency and drift, and a separate policy for retraining decisions.
