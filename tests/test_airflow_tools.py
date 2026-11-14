from agent.tools.airflow_tools import AirflowTools


def test_lists_training_dag_and_successful_run():
    tool = AirflowTools()
    assert tool.list_dags().data["dags"] == ["ml_training_pipeline"]
    assert tool.dag_runs().data["runs"][-1]["state"] == "success"


def test_trigger_requires_confirmation():
    result = AirflowTools().trigger_training("ml_training_pipeline", confirmed=False)
    assert not result.ok
    assert "confirmed=true" in result.error


def test_trigger_rejects_dag_outside_allowlist():
    result = AirflowTools().trigger_training("delete_everything", confirmed=True)
    assert not result.ok
    assert "allowlist" in result.error


def test_live_mode_exchanges_credentials_for_a_bearer_token(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"access_token": "short-lived-token"}

    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("AIRFLOW_USERNAME", "airflow")
    monkeypatch.setenv("AIRFLOW_PASSWORD", "airflow")
    monkeypatch.setattr("agent.tools.airflow_tools.requests.post", lambda *args, **_: Response())
    assert AirflowTools()._headers() == {"Authorization": "Bearer short-lived-token"}
