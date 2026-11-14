"""Airflow training workflow with a blocking quality gate."""

from __future__ import annotations

from datetime import datetime, timedelta

try:
    from airflow.sdk import dag, task
except ImportError:  # Allows repository linting/tests without installing Airflow.
    dag = task = None


if dag and task:
    @dag(
        dag_id="ml_training_pipeline",
        start_date=datetime(2026, 1, 1),
        schedule=None,
        catchup=False,
        default_args={"retries": 2, "retry_delay": timedelta(minutes=2)},
        tags=["mlops", "training"],
    )
    def training_pipeline():
        @task
        def validate_data() -> dict:
            return {"valid": True, "rows": 1000}

        @task
        def preprocess(validation: dict) -> dict:
            if not validation["valid"]:
                raise ValueError("Data validation failed; preprocessing is blocked")
            return {"features": 18}

        @task
        def train_model(features: dict) -> dict:
            return {"model_uri": "runs:/run-027/model", "features": features["features"]}

        @task
        def evaluate_and_log_mlflow(model: dict) -> dict:
            return {"f1": 0.901, "model_uri": model["model_uri"]}

        @task
        def quality_gate(metrics: dict) -> dict:
            if metrics["f1"] < 0.85:
                raise ValueError("Quality gate failed: F1 is below 0.85")
            return {"promotable": True, **metrics}

        quality_gate(evaluate_and_log_mlflow(train_model(preprocess(validate_data()))))

    training_pipeline()
