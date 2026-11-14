"""Train and record a small, reproducible churn model in MLflow."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

import mlflow
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "raw" / "customer_churn.csv"


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def build_model(model_name: str) -> Pipeline:
    if model_name == "random_forest":
        estimator = RandomForestClassifier(n_estimators=120, max_depth=7, random_state=4016)
    else:
        estimator = LogisticRegression(max_iter=500, random_state=4016)
    preprocessing = ColumnTransformer(
        [
            ("numeric", "passthrough", ["tenure_months", "monthly_charge", "support_tickets"]),
            ("contract", OneHotEncoder(handle_unknown="ignore"), ["contract"]),
        ]
    )
    return Pipeline([("preprocess", preprocessing), ("model", estimator)])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["logistic_regression", "random_forest"], default="logistic_regression")
    parser.add_argument("--dataset-version", default="v1.0")
    args = parser.parse_args()

    import pandas as pd

    frame = pd.read_csv(DATASET)
    features = frame.drop(columns=["churn"])
    target = frame["churn"]
    train_x, test_x, train_y, test_y = train_test_split(
        features, target, test_size=0.25, random_state=4016, stratify=target
    )
    pipeline = build_model(args.model)
    pipeline.fit(train_x, train_y)
    predictions = pipeline.predict(test_x)
    metrics = {
        "f1": round(float(f1_score(test_y, predictions)), 4),
        "accuracy": round(float(accuracy_score(test_y, predictions)), 4),
    }

    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000"))
    mlflow.set_experiment("churn-classifier")
    with mlflow.start_run(run_name=args.model) as run:
        mlflow.log_params({"model": args.model, "random_state": 4016, "test_size": 0.25})
        mlflow.log_metrics(metrics)
        mlflow.set_tags(
            {
                "dataset_version": args.dataset_version,
                "dataset_path": str(DATASET.relative_to(ROOT)),
                "git_commit": git_commit(),
            }
        )
        summary = {**metrics, "run_id": run.info.run_id, "dataset_version": args.dataset_version}
        artifact = ROOT / "data" / "latest_metrics.json"
        artifact.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        mlflow.log_artifact(str(artifact), artifact_path="metrics")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
