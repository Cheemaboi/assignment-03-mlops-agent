"""Airflow 3 REST API adapter with explicit confirmation for DAG runs."""

from __future__ import annotations

import os
from datetime import UTC, datetime

import requests

from agent.tools.common import demo_mode, load_demo_state, result


class AirflowTools:
    approved_dags = {"ml_training_pipeline"}

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        base = os.getenv("AIRFLOW_BASE_URL", "http://localhost:8080").rstrip("/")
        token = os.getenv("AIRFLOW_TOKEN")
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = requests.request(method, f"{base}/api/v2{path}", headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()

    def list_dags(self):
        def action():
            if demo_mode():
                return {"dags": load_demo_state()["airflow"]["dags"]}, ["data/demo_state.json:airflow.dags"]
            return self._request("GET", "/dags"), ["Airflow REST GET /api/v2/dags"]

        return result("airflow.list_dags", action)

    def dag_runs(self, dag_id: str = "ml_training_pipeline"):
        def action():
            if demo_mode():
                runs = [r for r in load_demo_state()["airflow"]["runs"] if r["dag_id"] == dag_id]
                return {"dag_id": dag_id, "runs": runs}, ["data/demo_state.json:airflow.runs"]
            return self._request("GET", f"/dags/{dag_id}/dagRuns"), ["Airflow REST GET dagRuns"]

        return result("airflow.dag_runs", action)

    def failed_tasks(self, dag_id: str = "ml_training_pipeline", run_id: str | None = None):
        def action():
            if demo_mode():
                runs = [r for r in load_demo_state()["airflow"]["runs"] if r["dag_id"] == dag_id]
                if run_id:
                    runs = [r for r in runs if r["run_id"] == run_id]
                failed = [task for run in runs for task in run["tasks"] if task["state"] == "failed"]
                return {"failed_tasks": failed}, ["data/demo_state.json:airflow.runs.tasks"]
            if not run_id:
                raise ValueError("run_id is required when querying a live Airflow server")
            data = self._request("GET", f"/dags/{dag_id}/dagRuns/{run_id}/taskInstances")
            return {"failed_tasks": [t for t in data.get("task_instances", []) if t.get("state") == "failed"]}, ["Airflow REST GET taskInstances"]

        return result("airflow.failed_tasks", action)

    def trigger_training(self, dag_id: str, confirmed: bool):
        def action():
            if dag_id not in self.approved_dags:
                raise ValueError("This DAG is not on the approved training-DAG allowlist")
            if not confirmed:
                raise ValueError("Training changes workflow state. Repeat the request with confirmed=true.")
            if demo_mode():
                run_id = f"manual__{datetime.now(UTC).isoformat()}"
                return {"dag_id": dag_id, "run_id": run_id, "state": "queued", "mode": "demo"}, [
                    "approval confirmed", "data/demo_state.json:airflow"
                ]
            return self._request("POST", f"/dags/{dag_id}/dagRuns", {"logical_date": datetime.now(UTC).isoformat()}), ["Airflow REST POST dagRuns", "approval confirmed"]

        return result("airflow.trigger_training", action)
