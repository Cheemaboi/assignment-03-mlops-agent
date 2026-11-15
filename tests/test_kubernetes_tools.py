from agent.tools.kubernetes_tools import KubernetesTools


def test_deployment_is_healthy_with_two_replicas():
    result = KubernetesTools().deployment_status()
    assert result.ok
    assert result.data["healthy"] is True
    assert result.data["deployment"]["ready_replicas"] == 2


def test_unconfirmed_cluster_change_is_rejected():
    result = KubernetesTools().restart_deployment("churn-inference", confirmed=False)
    assert not result.ok
    assert "changes cluster state" in result.error


def test_log_request_for_unknown_pod_has_no_invented_logs():
    result = KubernetesTools().pod_logs("unknown")
    assert not result.ok
    assert result.data == {}


def test_deployment_version_and_pod_events_are_available():
    tool = KubernetesTools()
    assert tool.deployment_status().data["deployment"]["image"] == "mlops-agent:0.1.0"
    assert tool.pod_events("churn-inference-6cd9b8d94-pf7xj").data["events"][0]["reason"] == "Started"
