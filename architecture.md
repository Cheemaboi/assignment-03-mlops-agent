# Architecture notes

The project separates conversation handling from service-specific work. The FastAPI endpoint sends a question to `MLOpsAgent`; the agent chooses small tools rather than building an answer from assumptions. Each tool returns the same `ToolResult` shape, including its evidence source, error, request id, and duration.

```text
FastAPI / CLI -> MLOpsAgent -> DVC adapter
                            -> MLflow adapter
                            -> Airflow REST adapter
                            -> Kubernetes API adapter
                                      |
                              structured evidence -> answer
```

In `DEMO_MODE=true`, the adapters read `data/demo_state.json`. This makes the repository runnable for marking and lets tests stay offline. In live mode, the MLflow adapter uses `MlflowClient`, Airflow uses its REST API, and Kubernetes uses the official Python client. DVC commands are fixed allowlisted argument lists, not user-provided shell commands.

State-changing actions have two checks: they must target an allowlisted DAG or the configured namespace, and `confirmed=true` must be supplied. Read operations remain namespace-scoped. No token, secret, or configuration value is written to logs.

The Airflow DAG follows `validate_data -> preprocess -> train_model -> evaluate_and_log_mlflow -> quality_gate`. A validation failure stops downstream work; an F1 below 0.85 fails the quality gate before any promotion step.
