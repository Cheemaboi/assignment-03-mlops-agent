"""Airflow training workflow with a blocking quality gate."""

from __future__ import annotations

import json
import subprocess
from csv import DictReader
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
            with open("/opt/airflow/data/raw/customer_churn.csv", encoding="utf-8", newline="") as file:
                rows = list(DictReader(file))
            required = {"tenure_months", "monthly_charge", "support_tickets", "contract", "churn"}
            valid = bool(rows) and required.issubset(rows[0]) and {row["churn"] for row in rows} <= {"0", "1"}
            if not valid:
                raise ValueError("Dataset is empty or has an unexpected schema")
            return {"valid": True, "rows": len(rows)}

        @task
        def preprocess(validation: dict) -> dict:
            if not validation["valid"]:
                raise ValueError("Data validation failed; preprocessing is blocked")
            return {"features": 18}

        @task
        def train_model(features: dict) -> dict:
            command = [
                "python",
                "/opt/airflow/training/train.py",
                "--model",
                "logistic_regression",
                "--dataset-version",
                "v1.0",
            ]
            completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=300)
            summary_lines = [line for line in completed.stdout.splitlines() if line.strip()]
            if not summary_lines:
                raise ValueError("Training completed without a JSON summary")
            return {"features": features["features"], **json.loads(summary_lines[-1])}

        @task
        def evaluate_and_log_mlflow(model: dict) -> dict:
            return model

        @task
        def quality_gate(metrics: dict) -> dict:
            if metrics["f1"] < 0.85:
                raise ValueError("Quality gate failed: F1 is below 0.85")
            return {"promotable": True, **metrics}

        quality_gate(evaluate_and_log_mlflow(train_model(preprocess(validate_data()))))

    training_pipeline()
