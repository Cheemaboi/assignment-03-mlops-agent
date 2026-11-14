# Technical Report - MLOps AI Agent

## 1. Introduction

For this assignment, I built a small MLOps agent that brings together four tasks that are usually checked separately: finding the data version, checking MLflow experiments, looking at the Airflow pipeline, and checking whether the prediction API is healthy on Kubernetes. I wanted the agent to be useful without pretending it knows more than the tools tell it. That is why every operational statement in its answer comes from a tool result and the response also includes the evidence source.

I made the project work in two modes. The normal submission mode is an offline demo mode with recorded responses in `data/demo_state.json`. This keeps the tests reproducible. The same modules have live adapters for a DVC repository, an MLflow tracking server, the Airflow 3 API, and the Kubernetes Python client.

## 2. System design

The user can ask the agent through the command line or the FastAPI `/ask` endpoint. The orchestrator reads the request and calls only the tools needed for it. Each tool returns a `ToolResult` containing its name, success state, evidence, duration, request id, data, and error if there was one. This makes it possible to show what was checked and to avoid hiding failures.

The four integrations are DVC for data versions, MLflow for runs and model registry details, Airflow for training workflow operations, and Kubernetes for application diagnosis. The live MLflow adapter uses `MlflowClient`, not the web UI. The live Airflow adapter uses the Airflow 3 REST API, and the Kubernetes adapter uses the official Python client.

The training DAG is `validate_data -> preprocess -> train_model -> evaluate_and_log_mlflow -> quality_gate`. The tasks have retries and the quality gate raises an error when F1 is below 0.85. This is important because training should not silently become promotion.

## 3. Permissions and safety decisions

The project does not execute a command copied from a user question. DVC operations use fixed argument lists. Airflow triggers are limited to `ml_training_pipeline`, and Kubernetes reads use the configured `mlops-demo` namespace. Both an Airflow trigger and a Kubernetes restart need `confirmed=true` in a separate request field. Secrets stay in environment variables and the structured log helper removes values whose key suggests a token or secret.

The agent also treats uncertainty as a real result. If MLflow times out, it says the best-model check is unavailable. It does not create a fallback answer from old language-model knowledge. Similarly, it does not recommend retraining merely because a user asks the question; there needs to be a clear freshness-policy breach, failed quality gate, or degradation result.

## 4. Exported demonstration evidence

The following evidence was exported by the project in demo mode. The files are included in the `evidence` folder so the values can be checked without reading the report.

| Area | Result recorded by the tool | What it shows |
| --- | --- | --- |
| DVC | `customer_churn`, version `v2.1`, Git `a4c92e1` | A training-data reference is present and reproducible. |
| MLflow | `run-027` (`xgboost-tuned`), F1 `0.901` | This is the strongest F1 candidate among the recorded finished runs. |
| Airflow | `ml_training_pipeline`, latest run `success` | All five pipeline stages completed in the demo record. |
| Kubernetes | `churn-inference`, 2/2 ready replicas | The Deployment is healthy and exposed by a ClusterIP Service. |

The model is still in the Staging registry stage. That is deliberate: F1 is useful for selecting a candidate, but it is not enough by itself to approve a production model.

## 5. Five agent conversations tested

1. **Which dataset version was used?** The DVC tool returned `v2.1` and commit `a4c92e1`. It also provides the reproduction command `git checkout a4c92e1 && dvc pull`.
2. **Compare the last runs and select a candidate.** MLflow returned three completed demo runs. `run-027` had F1 0.901, higher than 0.887 and 0.842. The agent recommends reviewing validation, fairness, latency, and approval checks before promotion.
3. **What happened in the training pipeline?** Airflow returned the most recent run as `success`, with validation, preprocessing, training, MLflow logging, and the quality gate all successful.
4. **Is the prediction API available?** Kubernetes returned 2 of 2 ready replicas for `churn-inference` and a ClusterIP Service forwarding port 80 to 8000. The demo Pod log also showed a successful `/healthz` response.
5. **Find the best model, data version, deployment status, and whether retraining is needed.** The agent used MLflow, DVC, Kubernetes, and Airflow in one response. It identified `run-027`, the `v2.1` data version, a healthy deployment, and a successful pipeline. It did not trigger retraining because no degradation, policy failure, or failed quality gate was present.

## 6. Failure investigations

### Case 1 - A training request without confirmation

I tried to trigger the Airflow DAG without setting `confirmed=true`. The tool rejected the request and returned a message saying that the action changes workflow state. The cause was not an Airflow outage; it was the intentional safety check. The resolution is to show the request to the user and only resend it with explicit confirmation.

### Case 2 - MLflow information unavailable

I mocked a timeout from the MLflow best-run tool. The agent kept the deployment and Airflow facts that were available, but placed the MLflow timeout under uncertainties and did not claim there was a best model. The root cause would need to be investigated as an MLflow service/network issue in a live setup. The immediate resolution is to check the tracking URI, token, server health, and network connection, then repeat the request.

I also tested an unconfirmed Kubernetes restart and an unknown Pod. Both are rejected without returning invented output. These checks are covered by the automated tests.

## 7. Testing and CI

The repository has 15 pytest tests and a GitHub Actions workflow that runs Ruff and pytest on pushes and pull requests. The tests mock unavailable external services through demo data and cover normal responses, invalid requests, authorization checks, and an unavailable-tool case. This is useful because a normal CI runner should not need access to a university cluster or personal credentials.

## 8. Limitations and next steps

The main limitation is that the included evidence is a reproducible local demo, not a permanently running cluster. For a production version I would add RBAC service accounts, an Airflow token with a limited role, real MLflow artifact storage, monitoring for latency/data drift, and a policy file for retraining thresholds. I would also replace the simple keyword router with an LLM tool-calling layer that is restricted to the same schemas and permissions. The safety layer should remain outside the model so that an unusual prompt cannot bypass it.
