"""Create a simple print-ready PDF version of the technical report."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

HERE = Path(__file__).resolve().parent
OUT = HERE / "MLOps_AI_Agent_Technical_Report.pdf"


def para(text, style):
    return Paragraph(text, style)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.black)
    canvas.drawCentredString(letter[0] / 2, 0.45 * inch, "MLOps and Production AI Engineering - Assignment 03")
    canvas.restoreState()


def main():
    doc = SimpleDocTemplate(str(OUT), pagesize=letter, leftMargin=0.82 * inch, rightMargin=0.82 * inch, topMargin=0.74 * inch, bottomMargin=0.68 * inch)
    styles = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=styles["BodyText"], fontName="Helvetica", fontSize=10.5, leading=14, spaceAfter=8, textColor=colors.black)
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=14, leading=17, spaceBefore=12, spaceAfter=6, textColor=colors.black)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11.5, leading=14, spaceBefore=9, spaceAfter=4, textColor=colors.black)
    title = ParagraphStyle("title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=24, alignment=TA_CENTER, textColor=colors.black, spaceAfter=7)
    sub = ParagraphStyle("sub", parent=body, alignment=TA_CENTER, spaceAfter=18)
    story = [para("MLOps AI Agent Technical Report", title), para("Assignment 03 | MLOps and Production AI Engineering | Fall 2026", sub)]
    story += [para("1. Introduction", h1), para("For this assignment, I built a small MLOps agent that brings together four tasks that are usually checked separately: finding the data version, checking MLflow experiments, looking at the Airflow pipeline, and checking whether the prediction API is healthy on Kubernetes. I wanted the agent to be useful without pretending it knows more than the tools tell it. For that reason, operational statements in its answer come from tool results and the response keeps the evidence source.", body), para("The project works in two modes. The normal submission mode is an offline demo mode with recorded responses in data/demo_state.json, which keeps the tests reproducible. The same modules have live adapters for DVC, an MLflow tracking server, the Airflow 3 API, and the Kubernetes Python client.", body)]
    story += [para("2. System design", h1), para("The user can ask the agent through the command line or the FastAPI /ask endpoint. The orchestrator reads the request and calls only the tools needed for it. Each tool returns a ToolResult with its name, success state, evidence, duration, request id, data, and an error if there was one. This makes it possible to show what was checked and to avoid hiding failures.", body)]
    for text in ["DVC: dataset listing, recorded version and Git commit, comparison, change detection, and reproduction instructions.", "MLflow: experiment/run listing, run details, metric-based candidate selection, and model registry information. Live mode uses MlflowClient rather than the web UI.", "Airflow: DAG and run status, failed task checks, and an approved training trigger through the Airflow 3 REST API.", "Kubernetes: workload, deployment, Service, and Pod-log checks through the official Kubernetes Python client."]:
        story.append(para("&bull; " + text, body))
    story += [para("The training DAG follows validate_data, preprocess, train_model, evaluate_and_log_mlflow, and quality_gate. Tasks have retries, and the quality gate raises an error when F1 is below 0.85. A failed validation or quality gate therefore blocks downstream promotion.", body), para("3. Tool permissions and safety", h1), para("The project does not execute a command copied from a user question. DVC operations use fixed argument lists. Airflow triggers are limited to ml_training_pipeline, and Kubernetes reads use the configured mlops-demo namespace. Both an Airflow trigger and a Kubernetes restart need confirmed=true in a separate request field. Secrets stay in environment variables and the structured logger removes values whose key suggests a token or secret.", body), para("The agent also treats uncertainty as a real result. If MLflow times out, it says that the best-model check is unavailable. It does not create a fallback answer from model knowledge. It also does not recommend retraining just because a user asks; there needs to be a freshness-policy breach, failed quality gate, or degradation result.", body)]
    story += [para("4. Exported demonstration evidence", h1), para("The following evidence was exported by the project in demo mode. The matching JSON files are in the evidence folder, so the values can be checked without relying only on this report.", body)]
    table_text = ParagraphStyle("table", parent=body, fontSize=8, leading=10, spaceAfter=0)
    header_text = ParagraphStyle("table_header", parent=table_text, fontName="Helvetica-Bold", textColor=colors.white)
    data = [[para("Area", header_text), para("Recorded tool result", header_text), para("What it shows", header_text)], [para("DVC", table_text), para("customer_churn, v2.1, Git a4c92e1", table_text), para("A training-data reference is present and reproducible.", table_text)], [para("MLflow", table_text), para("run-027 (xgboost-tuned), F1 0.901", table_text), para("Strongest F1 candidate among recorded finished runs.", table_text)], [para("Airflow", table_text), para("ml_training_pipeline, latest run success", table_text), para("All five workflow stages completed in the demo record.", table_text)], [para("Kubernetes", table_text), para("churn-inference, 2/2 ready replicas", table_text), para("Deployment is healthy behind a ClusterIP Service.", table_text)]]
    table = Table(data, colWidths=[0.8 * inch, 2.35 * inch, 2.84 * inch], repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#404040")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTNAME", (0, 1), (-1, -1), "Helvetica"), ("FONTSIZE", (0, 0), (-1, -1), 8.7), ("LEADING", (0, 0), (-1, -1), 11), ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9D9D9")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#F2F2F2")), ("BACKGROUND", (0, 4), (-1, 4), colors.HexColor("#F2F2F2"))]))
    story += [table, Spacer(1, 10), para("The selected model is still in the Staging registry stage. This is deliberate: F1 helps choose a candidate, but it is not enough on its own to approve a production model.", body)]
    story += [para("5. Five agent conversations tested", h1)]
    conversations = [("Which dataset version was used?", "The DVC tool returned v2.1 and commit a4c92e1. It also produced the reproduction command git checkout a4c92e1 && dvc pull."), ("Compare the last runs and select a candidate.", "MLflow returned three completed demo runs. run-027 had F1 0.901, above 0.887 and 0.842. The agent still recommends validation, fairness, latency, and approval checks before promotion."), ("What happened in the training pipeline?", "Airflow returned the most recent run as success, with validation, preprocessing, training, MLflow logging, and the quality gate all successful."), ("Is the prediction API available?", "Kubernetes returned 2 of 2 ready replicas for churn-inference and a ClusterIP Service forwarding port 80 to 8000. The demo Pod log also showed a successful /healthz response."), ("Find the best model, data version, deployment status, and whether retraining is needed.", "The agent used MLflow, DVC, Kubernetes, and Airflow in one response. It did not trigger retraining because no degradation, policy failure, or failed quality gate was present.")]
    for number, (question, answer) in enumerate(conversations, start=1):
        story.append(para(f"{number}. <b>{question}</b> {answer}", body))
    story += [para("6. Failure investigations", h1), para("Case 1 - A training request without confirmation", h2), para("I tried to trigger the Airflow DAG without setting confirmed=true. The tool rejected the request and explained that the action changes workflow state. The cause was not an Airflow outage; it was the intended safety check. The resolution is to show the action to the user and only resend it after explicit confirmation.", body), para("Case 2 - MLflow information unavailable", h2), para("I mocked a timeout from the MLflow best-run tool. The agent kept the deployment and Airflow facts that were available, but put the MLflow timeout under uncertainties and did not claim there was a best model. In a live setup, I would check the tracking URI, token, server health, and network connection before repeating the request.", body), para("I also tested an unconfirmed Kubernetes restart and an unknown Pod. Both are rejected without returning invented output. These checks are covered by the automated tests.", body)]
    story += [para("7. Testing and CI", h1), para("The repository has 15 pytest tests and a GitHub Actions workflow that runs Ruff and pytest on pushes and pull requests. The tests cover normal responses, invalid requests, authorization checks, tool selection, and an unavailable-tool case. The external services are mocked through demo data, so normal CI does not need cluster access or personal credentials.", body), para("8. Limitations and next steps", h1), para("The included evidence is a reproducible local demo, not a permanently running cluster. For a production version, I would add RBAC service accounts, an Airflow token with a limited role, real MLflow artifact storage, monitoring for latency and data drift, and a policy file for retraining thresholds. I would also replace the simple keyword router with an LLM tool-calling layer restricted to the same schemas and permissions. The safety checks should stay outside the model so an unusual prompt cannot bypass them.", body)]
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    main()
