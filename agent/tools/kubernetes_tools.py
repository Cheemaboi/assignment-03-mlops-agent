"""Kubernetes adapter. Reads are namespace-scoped; mutations require a second confirmation."""

from __future__ import annotations

import os

from agent.tools.common import demo_mode, load_demo_state, result


class KubernetesTools:
    def __init__(self, namespace: str | None = None):
        self.namespace = namespace or os.getenv("APPROVED_NAMESPACE", "mlops-demo")

    def _clients(self):
        try:
            from kubernetes import client, config
        except ImportError as exc:
            raise RuntimeError("Kubernetes client is not installed. Install the 'live' project extra.") from exc
        config.load_kube_config()
        return client.AppsV1Api(), client.CoreV1Api()

    def list_workloads(self):
        def action():
            if demo_mode():
                state = load_demo_state()["kubernetes"]
                return {"namespace": self.namespace, "deployment": state["deployment"], "pods": state["pods"]}, ["data/demo_state.json:kubernetes"]
            apps, core = self._clients()
            deployments = apps.list_namespaced_deployment(self.namespace).items
            pods = core.list_namespaced_pod(self.namespace).items
            return {"namespace": self.namespace, "deployments": [{"name": x.metadata.name, "ready": x.status.ready_replicas or 0} for x in deployments], "pods": [{"name": x.metadata.name, "phase": x.status.phase} for x in pods]}, ["Kubernetes AppsV1Api", "Kubernetes CoreV1Api"]

        return result("kubernetes.list_workloads", action)

    def deployment_status(self, name: str = "churn-inference"):
        def action():
            if demo_mode():
                deployment = load_demo_state()["kubernetes"]["deployment"]
                if name != deployment["name"]:
                    raise ValueError(f"Deployment '{name}' was not found in the approved namespace")
                healthy = deployment["ready_replicas"] >= deployment["desired_replicas"]
                return {"deployment": {**deployment, "image": "mlops-agent:0.1.0"}, "healthy": healthy, "namespace": self.namespace}, ["data/demo_state.json:kubernetes.deployment"]
            apps, _ = self._clients()
            item = apps.read_namespaced_deployment_status(name, self.namespace)
            desired = item.spec.replicas or 0
            ready = item.status.ready_replicas or 0
            containers = item.spec.template.spec.containers or []
            image = containers[0].image if containers else "unknown"
            deployment = {"name": name, "desired_replicas": desired, "ready_replicas": ready, "image": image}
            return {"deployment": deployment, "healthy": ready >= desired, "namespace": self.namespace}, ["Kubernetes AppsV1Api.read_namespaced_deployment_status"]

        return result("kubernetes.deployment_status", action)

    def service_status(self, name: str = "churn-inference"):
        def action():
            if demo_mode():
                service = load_demo_state()["kubernetes"]["service"]
                return {"service": service, "namespace": self.namespace}, ["data/demo_state.json:kubernetes.service"]
            _, core = self._clients()
            service = core.read_namespaced_service(name, self.namespace)
            return {"name": name, "type": service.spec.type, "ports": [{"port": p.port, "target_port": str(p.target_port)} for p in service.spec.ports]}, ["Kubernetes CoreV1Api.read_namespaced_service"]

        return result("kubernetes.service_status", action)

    def pod_logs(self, pod_name: str):
        def action():
            if demo_mode():
                pods = load_demo_state()["kubernetes"]["pods"]
                if not any(p["name"] == pod_name for p in pods):
                    raise ValueError("Pod was not found in the approved namespace")
                return {"pod": pod_name, "logs": "INFO: application started; GET /healthz 200"}, ["data/demo_state.json:kubernetes.pods"]
            _, core = self._clients()
            return {"pod": pod_name, "logs": core.read_namespaced_pod_log(pod_name, self.namespace, tail_lines=100)}, ["Kubernetes CoreV1Api.read_namespaced_pod_log"]

        return result("kubernetes.pod_logs", action)

    def pod_events(self, pod_name: str):
        """Return recent namespace-scoped events for diagnosis without mutating the cluster."""
        def action():
            if demo_mode():
                pods = load_demo_state()["kubernetes"]["pods"]
                if not any(p["name"] == pod_name for p in pods):
                    raise ValueError("Pod was not found in the approved namespace")
                return {"pod": pod_name, "events": [{"type": "Normal", "reason": "Started", "message": "Container started successfully"}]}, ["data/demo_state.json:kubernetes.pods"]
            _, core = self._clients()
            events = core.list_namespaced_event(self.namespace, field_selector=f"involvedObject.name={pod_name}").items
            return {"pod": pod_name, "events": [{"type": event.type, "reason": event.reason, "message": event.message} for event in events[-20:]]}, ["Kubernetes CoreV1Api.list_namespaced_event"]

        return result("kubernetes.pod_events", action)

    def restart_deployment(self, name: str, confirmed: bool):
        def action():
            if not confirmed:
                raise ValueError("Restarting changes cluster state. Repeat the request with confirmed=true.")
            if demo_mode():
                return {"deployment": name, "namespace": self.namespace, "action": "restart accepted in demo"}, ["approval confirmed"]
            apps, _ = self._clients()
            apps.patch_namespaced_deployment(name, self.namespace, {"spec": {"template": {"metadata": {"annotations": {"mlops-agent/restarted": "confirmed"}}}}})
            return {"deployment": name, "namespace": self.namespace, "action": "restart requested"}, ["Kubernetes AppsV1Api.patch_namespaced_deployment", "approval confirmed"]

        return result("kubernetes.restart_deployment", action)
