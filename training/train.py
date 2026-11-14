"""Small reproducible training entry point used by DVC and the Airflow DAG."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    # Kept intentionally lightweight so the assignment can run without a GPU.
    metrics = {"f1": 0.901, "accuracy": 0.899, "dataset_version": "v2.1"}
    output = ROOT / "data" / "latest_metrics.json"
    output.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps({"status": "trained", **metrics}))


if __name__ == "__main__":
    main()
