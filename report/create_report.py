"""Create the submission report with plain, student-report formatting."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

HERE = Path(__file__).resolve().parent
OUT = HERE / "MLOps_AI_Agent_Technical_Report.docx"


def shade(cell, fill: str) -> None:
    props = cell._tc.get_or_add_tcPr()
    element = OxmlElement("w:shd")
    element.set(qn("w:fill"), fill)
    props.append(element)


def set_font(run, size: float = 11, bold: bool = False) -> None:
    run.font.name = "Aptos"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor(0, 0, 0)


def add_body(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(7)
    p.paragraph_format.line_spacing = 1.15
    set_font(p.add_run(text))


def add_heading(doc: Document, text: str, level: int = 1) -> None:
    p = doc.add_paragraph()
    p.style = f"Heading {level}"
    p.paragraph_format.space_before = Pt(14 if level == 1 else 9)
    p.paragraph_format.space_after = Pt(5)
    set_font(p.add_run(text), 14 if level == 1 else 12, bold=True)


def add_bullet(doc: Document, text: str) -> None:
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(4)
    set_font(p.add_run(text))


def add_numbered(doc: Document, lead: str, rest: str) -> None:
    p = doc.add_paragraph(style="List Number")
    p.paragraph_format.space_after = Pt(5)
    set_font(p.add_run(lead), bold=True)
    set_font(p.add_run(rest))


def add_evidence_table(doc: Document) -> None:
    rows = [
        ("DVC", "customer_churn, v2.1, Git a4c92e1", "The training-data reference is present and reproducible."),
        ("MLflow", "run-027 (xgboost-tuned), F1 0.901", "The strongest F1 candidate among recorded finished runs."),
        ("Airflow", "ml_training_pipeline, latest run success", "All five workflow stages completed in the demo record."),
        ("Kubernetes", "churn-inference, 2/2 ready replicas", "The Deployment is healthy behind a ClusterIP Service."),
    ]
    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    table.autofit = False
    widths = (Inches(1.0), Inches(2.65), Inches(3.0))
    headers = ("Area", "Recorded tool result", "What it shows")
    for idx, text in enumerate(headers):
        cell = table.rows[0].cells[idx]
        cell.width = widths[idx]
        shade(cell, "404040")
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        set_font(run, 9.5, bold=True)
        run.font.color.rgb = RGBColor(255, 255, 255)
    for row in rows:
        cells = table.add_row().cells
        for idx, text in enumerate(row):
            cells[idx].width = widths[idx]
            cells[idx].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if len(table.rows) % 2 == 1:
                shade(cells[idx], "F2F2F2")
            p = cells[idx].paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            set_font(p.add_run(text), 9.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)


def main() -> None:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)

    normal = doc.styles["Normal"]
    normal.font.name = "Aptos"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    normal.font.size = Pt(11)
    for style_name in ("Heading 1", "Heading 2"):
        style = doc.styles[style_name]
        style.font.name = "Aptos"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
        style.font.color.rgb = RGBColor(0, 0, 0)

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(8)
    set_font(title.add_run("MLOps AI Agent Technical Report"), 20, bold=True)
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_after = Pt(22)
    set_font(subtitle.add_run("Assignment 03 | MLOps and Production AI Engineering | Fall 2026"), 11)

    add_heading(doc, "1. Introduction")
    add_body(doc, "For this assignment, I built a small MLOps agent that brings together four tasks that are usually checked separately: finding the data version, checking MLflow experiments, looking at the Airflow pipeline, and checking whether the prediction API is healthy on Kubernetes. I wanted the agent to be useful without pretending it knows more than the tools tell it. For that reason, operational statements in its answer come from tool results and the response keeps the evidence source.")
    add_body(doc, "The project works in two modes. The normal submission mode is an offline demo mode with recorded responses in data/demo_state.json, which keeps the tests reproducible. The same modules have live adapters for DVC, an MLflow tracking server, the Airflow 3 API, and the Kubernetes Python client.")

    add_heading(doc, "2. System design")
    add_body(doc, "The user can ask the agent through the command line or the FastAPI /ask endpoint. The orchestrator reads the request and calls only the tools needed for it. Each tool returns a ToolResult with its name, success state, evidence, duration, request id, data, and an error if there was one. This makes it possible to show what was checked and to avoid hiding failures.")
    add_bullet(doc, "DVC: dataset listing, recorded version and Git commit, comparison, change detection, and reproduction instructions.")
    add_bullet(doc, "MLflow: experiment/run listing, run details, metric-based candidate selection, and model registry information. Live mode uses MlflowClient rather than the web UI.")
    add_bullet(doc, "Airflow: DAG and run status, failed task checks, and an approved training trigger through the Airflow 3 REST API.")
    add_bullet(doc, "Kubernetes: workload, deployment, Service, and Pod-log checks through the official Kubernetes Python client.")
    add_body(doc, "The training DAG follows validate_data, preprocess, train_model, evaluate_and_log_mlflow, and quality_gate. Tasks have retries, and the quality gate raises an error when F1 is below 0.85. A failed validation or quality gate therefore blocks downstream promotion.")

    add_heading(doc, "3. Tool permissions and safety")
    add_body(doc, "The project does not execute a command copied from a user question. DVC operations use fixed argument lists. Airflow triggers are limited to ml_training_pipeline, and Kubernetes reads use the configured mlops-demo namespace. Both an Airflow trigger and a Kubernetes restart need confirmed=true in a separate request field. Secrets stay in environment variables and the structured logger removes values whose key suggests a token or secret.")
    add_body(doc, "The agent also treats uncertainty as a real result. If MLflow times out, it says that the best-model check is unavailable. It does not create a fallback answer from model knowledge. It also does not recommend retraining just because a user asks; there needs to be a freshness-policy breach, failed quality gate, or degradation result.")

    add_heading(doc, "4. Exported demonstration evidence")
    add_body(doc, "The following evidence was exported by the project in demo mode. The matching JSON files are in the evidence folder, so the values can be checked without relying only on this report.")
    add_evidence_table(doc)
    add_body(doc, "The selected model is still in the Staging registry stage. This is deliberate: F1 helps choose a candidate, but it is not enough on its own to approve a production model.")

    add_heading(doc, "5. Five agent conversations tested")
    add_numbered(doc, "Which dataset version was used? ", "The DVC tool returned v2.1 and commit a4c92e1. It also produced the reproduction command git checkout a4c92e1 && dvc pull.")
    add_numbered(doc, "Compare the last runs and select a candidate. ", "MLflow returned three completed demo runs. run-027 had F1 0.901, above 0.887 and 0.842. The agent still recommends validation, fairness, latency, and approval checks before promotion.")
    add_numbered(doc, "What happened in the training pipeline? ", "Airflow returned the most recent run as success, with validation, preprocessing, training, MLflow logging, and the quality gate all successful.")
    add_numbered(doc, "Is the prediction API available? ", "Kubernetes returned 2 of 2 ready replicas for churn-inference and a ClusterIP Service forwarding port 80 to 8000. The demo Pod log also showed a successful /healthz response.")
    add_numbered(doc, "Find the best model, data version, deployment status, and whether retraining is needed. ", "The agent used MLflow, DVC, Kubernetes, and Airflow in one response. It identified run-027, the v2.1 data version, a healthy deployment, and a successful pipeline. It did not trigger retraining because no degradation, policy failure, or failed quality gate was present.")

    add_heading(doc, "6. Failure investigations")
    add_heading(doc, "Case 1 - A training request without confirmation", level=2)
    add_body(doc, "I tried to trigger the Airflow DAG without setting confirmed=true. The tool rejected the request and explained that the action changes workflow state. The cause was not an Airflow outage; it was the intended safety check. The resolution is to show the action to the user and only resend it after explicit confirmation.")
    add_heading(doc, "Case 2 - MLflow information unavailable", level=2)
    add_body(doc, "I mocked a timeout from the MLflow best-run tool. The agent kept the deployment and Airflow facts that were available, but put the MLflow timeout under uncertainties and did not claim there was a best model. In a live setup, I would check the tracking URI, token, server health, and network connection before repeating the request.")
    add_body(doc, "I also tested an unconfirmed Kubernetes restart and an unknown Pod. Both are rejected without returning invented output. These checks are covered by the automated tests.")

    add_heading(doc, "7. Testing and CI")
    add_body(doc, "The repository has 15 pytest tests and a GitHub Actions workflow that runs Ruff and pytest on pushes and pull requests. The tests cover normal responses, invalid requests, authorization checks, tool selection, and an unavailable-tool case. The external services are mocked through demo data, so normal CI does not need cluster access or personal credentials.")

    add_heading(doc, "8. Limitations and next steps")
    add_body(doc, "The included evidence is a reproducible local demo, not a permanently running cluster. For a production version, I would add RBAC service accounts, an Airflow token with a limited role, real MLflow artifact storage, monitoring for latency and data drift, and a policy file for retraining thresholds. I would also replace the simple keyword router with an LLM tool-calling layer restricted to the same schemas and permissions. The safety checks should stay outside the model so an unusual prompt cannot bypass them.")

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(footer.add_run("MLOps and Production AI Engineering - Assignment 03"), 8.5)
    doc.save(OUT)


if __name__ == "__main__":
    main()
