from agent.tools.mlflow_tools import MLflowTools


def test_best_run_uses_recorded_f1():
    result = MLflowTools().best_run("f1")
    assert result.ok
    assert result.data["best_run"]["run_id"] == "run-027"
    assert result.data["best_run"]["f1"] == 0.901


def test_registry_information_is_available():
    result = MLflowTools().model_registry()
    assert result.ok
    assert result.data["stage"] == "Staging"


def test_invalid_metric_does_not_produce_a_made_up_best_run():
    result = MLflowTools().best_run("does_not_exist")
    assert not result.ok
    assert result.data == {}
