"""Simple command-line entry point for a local agent conversation."""

from __future__ import annotations

import argparse
import json

from agent.orchestrator import MLOpsAgent


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the MLOps operations agent a question.")
    parser.add_argument("question")
    parser.add_argument("--confirm", action="store_true", help="Confirm an approved state-changing request")
    args = parser.parse_args()
    print(json.dumps(MLOpsAgent().ask(args.question, confirmed=args.confirm).to_dict(), indent=2))


if __name__ == "__main__":
    main()
