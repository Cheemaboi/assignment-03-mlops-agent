from agent.tools.dvc_tools import DVCTools


def test_lists_tracked_dataset():
    result = DVCTools().list_datasets()
    assert result.ok
    assert result.data["datasets"][0]["name"] == "customer_churn"


def test_reports_recorded_version_and_commit():
    result = DVCTools().get_dataset_version()
    assert result.ok
    assert result.data["dataset_version"] == "v2.1"
    assert result.data["git_commit"] == "a4c92e1"


def test_reproduction_command_is_pinned_to_a_revision():
    result = DVCTools().reproduce_revision("v2.0")
    assert result.ok
    assert "git checkout 9c4d2f0" in result.data["reproduction_command"]


def test_unknown_dataset_is_rejected():
    result = DVCTools().get_dataset_version("not-tracked")
    assert not result.ok
    assert "not tracked" in result.error
