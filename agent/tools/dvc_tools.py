"""DVC provenance tools. Live mode only uses an allowlisted DVC command surface."""

from __future__ import annotations

import json
from pathlib import Path

from agent.tools.common import allowed_subprocess, demo_mode, load_demo_state, result


class DVCTools:
    @staticmethod
    def _live_provenance() -> dict:
        """Load the repository's version label without accepting caller-provided paths."""
        source = Path("data/provenance.json")
        return json.loads(source.read_text(encoding="utf-8"))

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
            provenance = self._live_provenance()
            if dataset != provenance["dataset"]:
                raise ValueError(f"Dataset '{dataset}' is not tracked in repository provenance")
            git_commit = allowed_subprocess(["git", "rev-parse", "HEAD"])
            status = allowed_subprocess(["dvc", "status"])
            return {
                "dataset": provenance["dataset"],
                "dataset_version": provenance["dataset_version"],
                "data_path": provenance["data_path"],
                "dvc_pointer": provenance["dvc_pointer"],
                "git_commit": git_commit,
                "dvc_status": status,
            }, ["data/provenance.json", "git rev-parse HEAD", "dvc status"]

        return result("dvc.get_dataset_version", action)

    def compare_versions(self, left: str, right: str):
        def action():
            if demo_mode():
                versions = load_demo_state()["dvc"]["revisions"]
            else:
                versions = self._live_provenance()["versions"]
            if left not in versions or right not in versions:
                raise ValueError("Both dataset revisions must be known tracked revisions")
            return {
                "left": left,
                "right": right,
                "left_commit": versions[left],
                "right_commit": versions[right],
                "same_revision": left == right,
            }, ["data/demo_state.json:dvc.revisions" if demo_mode() else "data/provenance.json:versions"]

        return result("dvc.compare_versions", action)

    def detect_changes(self):
        def action():
            if demo_mode():
                changed = load_demo_state()["dvc"]["changed"]
                return {"changed": changed}, ["data/demo_state.json:dvc.changed"]
            raw_status = allowed_subprocess(["dvc", "status", "--json"])
            return {"changed": bool(json.loads(raw_status))}, ["dvc status --json"]

        return result("dvc.detect_changes", action)

    def reproduce_revision(self, version: str):
        def action():
            if demo_mode():
                commit = load_demo_state()["dvc"]["revisions"].get(version)
            else:
                commit = self._live_provenance()["versions"].get(version)
            if not commit:
                raise ValueError(f"Unknown dataset version: {version}")
            command = f"git checkout {commit} && dvc pull"
            evidence = "data/demo_state.json:dvc.revisions" if demo_mode() else "data/provenance.json:versions"
            return {"version": version, "git_commit": commit, "reproduction_command": command}, [evidence]

        return result("dvc.reproduce_revision", action)
