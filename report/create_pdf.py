"""Build the plain, print-friendly submission report from verified local evidence."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

HERE = Path(__file__).resolve().parent


def paragraph(text, style):
    return Paragraph(text, style)


def footer(canvas, _doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.black)
    canvas.drawCentredString(letter[0] / 2, 0.42 * inch, "MLOps and Production AI Engineering - Assignment 03")
    canvas.restoreState()


def main():
    output = HERE / "MLOps_AI_Agent_Technical_Report.pdf"
    doc = SimpleDocTemplate(str(output), pagesize=letter, leftMargin=0.8 * inch, rightMargin=0.8 * inch, topMargin=0.7 * inch, bottomMargin=0.62 * inch)
    base = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=base["BodyText"], fontName="Helvetica", fontSize=10.3, leading=13.6, spaceAfter=8, textColor=colors.black)
    h1 = ParagraphStyle("h1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=14, leading=17, spaceBefore=12, spaceAfter=6, textColor=colors.black)
    title = ParagraphStyle("title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=19, leading=23, alignment=TA_CENTER, textColor=colors.black, spaceAfter=6)
    sub = ParagraphStyle("sub", parent=body, alignment=TA_CENTER, spaceAfter=17)
    story = [paragraph("MLOps AI Agent Technical Report", title), paragraph("Assignment 03 | MLOps and Production AI Engineering", sub)]
    story += [paragraph("1. What I built", h1), paragraph("For this assignment, I built a small MLOps assistant around four real operations: DVC data provenance, MLflow experiment tracking, an Airflow training workflow, and Kubernetes application checks. I kept the agent deterministic on purpose. It routes a request to approved tools instead of relying on an LLM to invent an answer, so every operational statement can be traced back to a tool response.", body), paragraph("There is no OpenAI dependency or API key in this project. Offline fixture mode keeps the tests repeatable, while the same adapters switch to local services when DEMO_MODE=false.", body)]
    story += [paragraph("2. Design and safety", h1), paragraph("The command-line program and FastAPI /ask endpoint call the same orchestrator. Every tool returns its success state, data, evidence source, duration, and an error where appropriate. The DVC adapter uses fixed DVC and Git commands. MLflow uses MlflowClient. Airflow exchanges local credentials for a short-lived bearer token before calling its version 3 REST API. Kubernetes uses the official Python client inside the approved mlops-demo namespace.", body), paragraph("The workflow is validate_data, preprocess, train_model, evaluate_and_log_mlflow, and quality_gate. Validation checks the CSV schema and class labels. The quality gate fails below F1 0.85. Airflow triggers and Kubernetes restarts require confirmed=true, and the agent never treats a chat question as a shell command.", body)]
    story += [paragraph("3. Live local verification", h1), paragraph("I ran the local services with Docker Desktop, a kind Kubernetes cluster, and the DVC repository in this project. The exported values are in evidence/live_local_run.json. Older evidence JSON files are offline test fixtures and are not presented as live output.", body)]
    small = ParagraphStyle("small", parent=body, fontSize=8.5, leading=10.5, spaceAfter=0)
    header = ParagraphStyle("header", parent=small, fontName="Helvetica-Bold", textColor=colors.white)
    table_data = [[paragraph("Area", header), paragraph("Live result", header), paragraph("What it proves", header)], [paragraph("DVC", small), paragraph("customer_churn v1.0; clean dvc status", small), paragraph("The synthetic CSV is DVC-tracked and the stage is reproducible.", small)], [paragraph("MLflow", small), paragraph("logistic regression; F1 0.9787; accuracy 0.9833", small), paragraph("MlflowClient selected the best completed run.", small)], [paragraph("Airflow", small), paragraph("manual run at 22:52:44 UTC; success", small), paragraph("All five workflow tasks completed.", small)], [paragraph("Kubernetes", small), paragraph("churn-inference 2/2 ready", small), paragraph("Two API replicas were healthy behind a ClusterIP Service.", small)]]
    table = Table(table_data, colWidths=[0.8 * inch, 2.3 * inch, 2.75 * inch], repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#404040")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9D9D9")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#F2F2F2")), ("BACKGROUND", (0, 4), (-1, 4), colors.HexColor("#F2F2F2"))]))
    story += [table, Spacer(1, 9), paragraph("4. Questions I tested", h1)]
    for item in ["Which dataset version was used? The DVC tool returned v1.0, its pointer file, and the Git revision.", "Which run is strongest? MLflow selected logistic regression at F1 0.9787, while still recommending validation, fairness, latency, and approval review before promotion.", "Did the pipeline finish? Airflow returned a successful manual run with validation, preprocessing, training, MLflow logging, and the quality gate all successful.", "Is the prediction API available? Kubernetes returned two ready churn-inference replicas and a ClusterIP Service on port 80.", "What is the overall MLOps status? One request used all four tools, found healthy services, and correctly did not recommend automatic retraining without a degradation or policy signal."]:
        story.append(paragraph("&bull; " + item, body))
    story += [paragraph("5. Problems found during local verification", h1), paragraph("The first Airflow attempt could not find the DVC-materialized CSV because the container had started before the file was restored. I recreated only the Airflow container and checked that the CSV was present before triggering the successful run.", body), paragraph("MLflow initially rejected local requests because its host allow-list did not include localhost:5000 and mlflow:5000. Adding those exact local hosts fixed both the laptop and container paths. I also changed the DAG to parse the final JSON line from training because MLflow prints a run URL before the script summary.", body), paragraph("6. Tests and limits", h1), paragraph("The repository has 16 pytest tests and a GitHub Actions workflow for Ruff and pytest. The local stack is for coursework rather than production: Airflow Standalone is local-only, the DVC remote is a local folder, and MLflow uses SQLite. A production version would add service-account RBAC, managed artifact storage, drift monitoring, and a separate retraining policy.", body)]
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    main()
