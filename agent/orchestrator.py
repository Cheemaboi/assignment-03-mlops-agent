"""Intent routing and evidence-first response composition.

The orchestrator is intentionally deterministic for the coursework demo. It calls real
adapters in live mode and never fills an unavailable tool response with a guessed claim.
"""

from __future__ import annotations

from uuid import uuid4

from agent.schemas import AgentResponse, ToolResult
from agent.tools.airflow_tools import AirflowTools
from agent.tools.dvc_tools import DVCTools
from agent.tools.kubernetes_tools import KubernetesTools
from agent.tools.mlflow_tools import MLflowTools


class MLOpsAgent:
    def __init__(self):
        self.dvc = DVCTools()
        self.mlflow = MLflowTools()
        self.airflow = AirflowTools()
        self.kubernetes = KubernetesTools()

    def ask(self, question: str, confirmed: bool = False) -> AgentResponse:
        request_id = str(uuid4())
        text = question.lower()
        results: list[ToolResult] = []
        multi_tool = any(word in text for word in ("best", "recent model", "retraining", "deployment"))
        if multi_tool:
            results.extend([self.mlflow.best_run("f1"), self.kubernetes.deployment_status(), self.airflow.dag_runs()])
            best = results[0]
            if best.ok:
                version = best.data["best_run"].get("dataset_version")
                if version:
                    results.append(self.dvc.get_dataset_version())
        else:
            if any(word in text for word in ("dataset", "dvc", "provenance", "version")):
                results.append(self.dvc.get_dataset_version())
            if any(word in text for word in ("experiment", "mlflow", "metric", "run")):
                results.append(self.mlflow.list_runs())
            if any(word in text for word in ("airflow", "dag", "pipeline", "trigger")):
                results.append(self.airflow.trigger_training("ml_training_pipeline", confirmed) if "trigger" in text else self.airflow.dag_runs())
            if any(word in text for word in ("kubernetes", "pod", "deployment", "api unavailable", "service")):
                results.append(self.kubernetes.deployment_status())
        if not results:
            return AgentResponse("I could not map that question to an approved operation. Try asking about dataset provenance, MLflow runs, an Airflow DAG, or the Kubernetes deployment.", request_id, [], [], [], [])
        return self._compose(results, request_id)

    @staticmethod
    def _compose(results: list[ToolResult], request_id: str) -> AgentResponse:
        successful = [item for item in results if item.ok]
        failed = [item for item in results if not item.ok]
        evidence = [entry for item in successful for entry in item.evidence]
        facts: list[str] = []
        actions: list[str] = []
        for item in successful:
            if item.tool == "mlflow.best_run":
                run = item.data["best_run"]
                facts.append(f"MLflow selected {run['run_id']} ({run['name']}) with F1 {run['f1']:.3f}.")
                actions.append("Review validation, fairness, latency, and approval criteria before production promotion.")
            elif item.tool == "dvc.get_dataset_version":
                facts.append(f"The recorded dataset is {item.data['dataset_version']} at Git commit {item.data['git_commit']}.")
            elif item.tool == "kubernetes.deployment_status":
                d = item.data["deployment"]
                facts.append(f"Kubernetes reports {d['ready_replicas']}/{d['desired_replicas']} ready replicas for {d['name']}.")
            elif item.tool == "airflow.dag_runs":
                runs = item.data["runs"]
                if runs:
                    latest = item.data.get("latest_run") or runs[-1]
                    facts.append(f"The latest recorded Airflow run is {latest['state']} ({latest['run_id']}).")
            elif item.tool == "mlflow.list_runs":
                facts.append(f"MLflow returned {len(item.data['runs'])} recorded run(s).")
            elif item.tool == "airflow.trigger_training":
                facts.append(f"The approved training DAG was accepted with run id {item.data['run_id']}.")
        uncertainties = [f"{item.tool} was unavailable: {item.error}" for item in failed]
        if not successful:
            facts.append("No operational conclusion is available because the requested tools did not return evidence.")
        if any(item.tool == "mlflow.best_run" for item in successful):
            actions.append("Do not retrain automatically: the current evidence contains no freshness-policy breach, failed quality gate, or degradation measurement.")
        return AgentResponse(" ".join(facts), request_id, [item.tool for item in results], evidence, uncertainties, actions)
