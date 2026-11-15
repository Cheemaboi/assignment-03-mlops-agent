"""MLflow tools use MlflowClient in live mode; fixtures are only for offline demo runs."""

from __future__ import annotations

import os

from agent.tools.common import demo_mode, load_demo_state, result


class MLflowTools:
    def _client(self):
        try:
            from mlflow import MlflowClient
        except ImportError as exc:
            raise RuntimeError("MLflow is not installed. Install the 'live' project extra.") from exc
        return MlflowClient(tracking_uri=os.getenv("MLFLOW_TRACKING_URI"))

    def list_experiments(self):
        def action():
            if demo_mode():
                exp = load_demo_state()["mlflow"]["experiment"]
                return {"experiments": [exp]}, ["data/demo_state.json:mlflow"]
            experiments = self._client().search_experiments()
            return {"experiments": [{"id": e.experiment_id, "name": e.name} for e in experiments]}, ["MlflowClient.search_experiments"]

        return result("mlflow.list_experiments", action)

    def list_runs(self, limit: int = 5):
        def action():
            if demo_mode():
                runs = load_demo_state()["mlflow"]["runs"][-limit:]
                return {"runs": runs}, ["data/demo_state.json:mlflow.runs"]
            client = self._client()
            experiment = client.get_experiment_by_name("churn-classifier")
            if experiment is None:
                raise RuntimeError("Experiment 'churn-classifier' was not found")
            runs = client.search_runs([experiment.experiment_id], max_results=limit, order_by=["attributes.start_time DESC"])
            formatted = []
            for run in runs:
                metrics = run.data.metrics
                formatted.append(
                    {
                        "run_id": run.info.run_id,
                        "name": run.data.tags.get("mlflow.runName", run.info.run_id),
                        "status": run.info.status,
                        "f1": metrics.get("f1"),
                        "accuracy": metrics.get("accuracy"),
                        "dataset_version": run.data.tags.get("dataset_version"),
                        "metrics": metrics,
                        "params": run.data.params,
                    }
                )
            return {"runs": formatted}, ["MlflowClient.search_runs"]

        return result("mlflow.list_runs", action)

    def get_run(self, run_id: str):
        def action():
            if demo_mode():
                for run in load_demo_state()["mlflow"]["runs"]:
                    if run["run_id"] == run_id:
                        return {"run": run}, ["data/demo_state.json:mlflow.runs"]
                raise ValueError(f"Run '{run_id}' was not found")
            run = self._client().get_run(run_id)
            return {"run_id": run.info.run_id, "metrics": run.data.metrics, "params": run.data.params, "tags": run.data.tags}, ["MlflowClient.get_run"]

        return result("mlflow.get_run", action)

    def compare_runs(self, metric: str = "f1", limit: int = 5):
        """Rank recent completed runs without implying that ranking is promotion."""
        def action():
            runs_result = self.list_runs(limit)
            if not runs_result.ok:
                raise RuntimeError(runs_result.error or "MLflow search failed")
            ranked = []
            for run in runs_result.data["runs"]:
                value = run.get(metric, run.get("metrics", {}).get(metric))
                if run.get("status") == "FINISHED" and value is not None:
                    ranked.append({"run_id": run["run_id"], "name": run.get("name"), metric: value})
            if len(ranked) < 2:
                raise ValueError(f"At least two finished runs with metric '{metric}' are required for comparison")
            ranked.sort(key=lambda run: run[metric], reverse=True)
            return {"metric": metric, "runs": ranked, "recommended_run": ranked[0]}, [
                "data/demo_state.json:mlflow.runs" if demo_mode() else "MlflowClient.search_runs"
            ]

        return result("mlflow.compare_runs", action)

    def best_run(self, metric: str = "f1"):
        def action():
            if demo_mode():
                runs = load_demo_state()["mlflow"]["runs"]
                candidates = [run for run in runs if metric in run and run["status"] == "FINISHED"]
                if not candidates:
                    raise ValueError(f"No finished runs contain metric '{metric}'")
                chosen = max(candidates, key=lambda item: item[metric])
                return {"metric": metric, "best_run": chosen, "candidate_count": len(candidates)}, ["data/demo_state.json:mlflow.runs"]
            # MLflow supports ordering directly, avoiding UI scraping.
            runs = self.list_runs(50)
            if not runs.ok:
                raise RuntimeError(runs.error or "MLflow search failed")
            candidates = [r for r in runs.data["runs"] if metric in r.get("metrics", {})]
            if not candidates:
                raise ValueError(f"No runs have metric '{metric}'")
            return {"metric": metric, "best_run": max(candidates, key=lambda r: r["metrics"][metric])}, ["MlflowClient.search_runs"]

        return result("mlflow.best_run", action)

    def model_registry(self):
        def action():
            if demo_mode():
                return load_demo_state()["mlflow"]["registry"], ["data/demo_state.json:mlflow.registry"]
            versions = self._client().search_model_versions("name='churn-classifier'")
            return {"versions": [{"version": v.version, "stage": v.current_stage, "run_id": v.run_id} for v in versions]}, ["MlflowClient.search_model_versions"]

        return result("mlflow.model_registry", action)
