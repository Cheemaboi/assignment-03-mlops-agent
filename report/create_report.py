"""Create the editable Word version of the submission report."""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

HERE = Path(__file__).resolve().parent


def add_heading(document, text, level=1):
    paragraph = document.add_heading(text, level=level)
    for run in paragraph.runs:
        run.font.color.rgb = RGBColor(0, 0, 0)


def add_paragraph(document, text):
    paragraph = document.add_paragraph(text)
    paragraph.paragraph_format.space_after = Pt(7)
    for run in paragraph.runs:
        run.font.size = Pt(10.5)


def main():
    document = Document()
    section = document.sections[0]
    section.top_margin = section.bottom_margin = Inches(0.7)
    section.left_margin = section.right_margin = Inches(0.8)
    title = document.add_heading("MLOps AI Agent Technical Report", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    document.add_paragraph("Assignment 03 | MLOps and Production AI Engineering").alignment = WD_ALIGN_PARAGRAPH.CENTER
    sections = [
        ("What I built", "I built a deterministic MLOps assistant for DVC provenance, MLflow experiment tracking, an Airflow workflow, and Kubernetes checks. It uses approved tools rather than an OpenAI model or API key, so each operational claim comes from a real tool response."),
        ("Design and safety", "The CLI and FastAPI endpoint share one orchestrator. DVC uses fixed commands, MLflow uses MlflowClient, Airflow uses an authenticated version 3 REST API, and Kubernetes uses the official Python client in mlops-demo. State-changing operations require confirmed=true. The workflow validates data, preprocesses it, trains, logs to MLflow, and blocks below F1 0.85."),
        ("Live local verification", "I ran Docker Desktop, MLflow, Airflow, DVC, and a kind Kubernetes cluster locally. DVC tracked customer_churn v1.0 with a clean status. The best MLflow logistic-regression run achieved F1 0.9787 and accuracy 0.9833. Airflow completed all five tasks in a successful manual run. Kubernetes reported churn-inference at 2/2 ready replicas behind a ClusterIP Service."),
        ("Checks and failures", "I checked data version, selected the best run, inspected the successful pipeline, checked the deployment, and made one combined MLOps request. During setup, I refreshed the Airflow bind mount after DVC restored the CSV, added port-qualified MLflow hosts to the local allow-list, and parsed the final training JSON line after MLflow printed its run URL."),
        ("Testing and limits", "The repository has 16 pytest tests plus Ruff in GitHub Actions. The stack is local coursework infrastructure: Airflow Standalone, a local DVC remote, and SQLite-backed MLflow. A production version would add RBAC, managed artifact storage, drift monitoring, and a dedicated retraining policy."),
    ]
    for heading, body in sections:
        add_heading(document, heading)
        add_paragraph(document, body)
    document.save(HERE / "MLOps_AI_Agent_Technical_Report.docx")


if __name__ == "__main__":
    main()
