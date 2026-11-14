from agent.orchestrator import MLOpsAgent
from agent.tools.mlflow_tools import MLflowTools


def test_multi_tool_question_collects_four_sources():
    response = MLOpsAgent().ask(
        "Find the best recent model, identify the dataset version, check deployment status, and explain whether retraining is necessary."
    )
    assert {"mlflow.best_run", "dvc.get_dataset_version", "kubernetes.deployment_status", "airflow.dag_runs"}.issubset(response.tools_used)
    assert "Do not retrain automatically" in response.recommended_actions[-1]


def test_unavailable_tool_is_reported_as_uncertainty_not_fact(monkeypatch):
    monkeypatch.setattr(MLflowTools, "best_run", lambda self, metric: type("R", (), {"tool": "mlflow.best_run", "ok": False, "error": "timeout", "data": {}, "evidence": []})())
    response = MLOpsAgent().ask("Find the best recent model and deployment status")
    assert any("timeout" in uncertainty for uncertainty in response.uncertainties)
    assert "MLflow selected" not in response.answer
