"""DVC provenance tools. Live mode only uses an allowlisted DVC command surface."""

from __future__ import annotations

from agent.tools.common import allowed_subprocess, demo_mode, load_demo_state, result


class DVCTools:
    def list_datasets(self):
        def action():
            if demo_mode():
                state = load_demo_state()["dvc"]
                return {"datasets": [{"name": state["dataset"], "path": state["data_path"]}]}, [
                    "data/demo_state.json:dvc"
                ]
            output = allowed_subprocess(["dvc", "data", "status"])
            return {"status": output}, ["dvc data status"]

        return result("dvc.list_datasets", action)

    def get_dataset_version(self, dataset: str = "customer_churn"):
        def action():
            if demo_mode():
                state = load_demo_state()["dvc"]
                if dataset != state["dataset"]:
                    raise ValueError(f"Dataset '{dataset}' is not tracked in demo provenance")
                return state, ["data/demo_state.json:dvc", f"git commit {state['git_commit']}"]
            git_commit = allowed_subprocess(["git", "rev-parse", "HEAD"])
            status = allowed_subprocess(["dvc", "status"])
            return {"dataset": dataset, "git_commit": git_commit, "dvc_status": status}, ["git rev-parse HEAD", "dvc status"]

        return result("dvc.get_dataset_version", action)

    def compare_versions(self, left: str, right: str):
        def action():
            state = load_demo_state()["dvc"]
            versions = state["revisions"]
            if left not in versions or right not in versions:
                raise ValueError("Both dataset revisions must be known tracked revisions")
            return {
                "left": left,
                "right": right,
                "left_commit": versions[left],
                "right_commit": versions[right],
                "same_revision": left == right,
            }, ["data/demo_state.json:dvc.revisions"]

        return result("dvc.compare_versions", action)

    def detect_changes(self):
        def action():
            if demo_mode():
                changed = load_demo_state()["dvc"]["changed"]
                return {"changed": changed}, ["data/demo_state.json:dvc.changed"]
            return {"changed": bool(allowed_subprocess(["dvc", "status", "--json"]))}, ["dvc status --json"]

        return result("dvc.detect_changes", action)

    def reproduce_revision(self, version: str):
        def action():
            state = load_demo_state()["dvc"]
            commit = state["revisions"].get(version)
            if not commit:
                raise ValueError(f"Unknown dataset version: {version}")
            command = f"git checkout {commit} && dvc pull"
            return {"version": version, "git_commit": commit, "reproduction_command": command}, [
                "data/demo_state.json:dvc.revisions"
            ]

        return result("dvc.reproduce_revision", action)
