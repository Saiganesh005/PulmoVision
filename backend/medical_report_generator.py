import io
from datetime import datetime

import numpy as np
import streamlit as st
import torch
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


DISCLAIMER = (
    "This AI-assisted report is for clinical decision support only and is not a final diagnosis or prescription. "
    "Medication information below lists classes and generic examples for educational context only. "
    "Definitive treatment decisions must be made by a licensed clinician after full clinical evaluation."
)


def calculate_severity(gradcam: np.ndarray) -> tuple[str, float]:
    """
    Severity from Grad-CAM mean intensity:
      < 0.3  -> Mild
      0.3-0.6 -> Moderate
      > 0.6  -> Severe
    """
    if gradcam is None:
        raise ValueError("gradcam cannot be None")

    heatmap = np.asarray(gradcam, dtype=np.float32)
    if heatmap.size == 0:
        raise ValueError("gradcam cannot be empty")

    # Normalize if heatmap appears to be in 0..255
    if heatmap.max() > 1.0:
        heatmap = heatmap / 255.0

    mean_intensity = float(np.clip(heatmap.mean(), 0.0, 1.0))

    if mean_intensity < 0.3:
        severity = "Mild"
    elif mean_intensity <= 0.6:
        severity = "Moderate"
    else:
        severity = "Severe"

    return severity, mean_intensity


def _normalize_probabilities(probabilities: list[float] | np.ndarray, labels: list[str]) -> dict[str, float]:
    scores = np.asarray(probabilities, dtype=np.float32).flatten()
    if scores.size != len(labels):
        raise ValueError("Length of probabilities must match disease labels")

    # Accept either raw logits/scores or already normalized values
    if np.any(scores < 0) or not np.isclose(scores.sum(), 1.0, atol=1e-3):
        scores = torch.softmax(torch.tensor(scores), dim=0).numpy()

    total = float(np.clip(scores.sum(), 1e-12, None))
    scores = scores / total
    return {labels[i]: float(scores[i]) for i in range(len(labels))}


def _medication_guidance(predicted_label: str) -> dict:
    label = predicted_label.strip().lower()

    if "covid" in label:
        return {
            "classes": [
                {
                    "class": "Antivirals",
                    "examples": ["remdesivir"],
                    "indication": "Typically considered in selected hospitalized patients under physician supervision.",
                },
                {
                    "class": "Anti-inflammatory corticosteroids",
                    "examples": ["dexamethasone"],
                    "indication": "Typically considered for patients with oxygen requirement/hypoxia.",
                },
                {
                    "class": "Antipyretic/analgesic",
                    "examples": ["paracetamol"],
                    "indication": "Commonly used for fever or discomfort relief.",
                },
                {
                    "class": "Anticoagulants",
                    "examples": ["heparin"],
                    "indication": "Considered in selected thrombotic-risk cases per clinical judgment.",
                },
            ],
            "care_pathway": "Home monitoring if clinically stable; outpatient/hospital escalation for hypoxia or worsening respiratory distress.",
        }

    if "pneumonia" in label:
        return {
            "classes": [
                {
                    "class": "Antibiotics (bacterial suspicion)",
                    "examples": ["amoxicillin-clavulanate", "azithromycin", "ceftriaxone"],
                    "indication": "Typically considered when bacterial etiology is clinically suspected.",
                },
                {
                    "class": "Antipyretic",
                    "examples": ["paracetamol"],
                    "indication": "Commonly used for fever and symptomatic comfort.",
                },
                {
                    "class": "Bronchodilators",
                    "examples": ["salbutamol"],
                    "indication": "May be considered when bronchospasm/wheeze is present.",
                },
                {
                    "class": "Oxygen therapy",
                    "examples": ["supplemental oxygen"],
                    "indication": "Considered when oxygen saturation is reduced.",
                },
            ],
            "care_pathway": "Outpatient care for mild stable cases; hospital care for hypoxia, multilobar disease, or systemic instability.",
        }

    if "normal" in label:
        return {
            "classes": [
                {
                    "class": "No pharmacotherapy indicated",
                    "examples": ["not applicable"],
                    "indication": "No major AI-detected pulmonary pathology on this image.",
                }
            ],
            "care_pathway": "Routine preventive care, symptom watch, and standard follow-up as clinically required.",
        }

    return {
        "classes": [
            {
                "class": "Clinician-directed therapy",
                "examples": ["condition-specific generic agents"],
                "indication": "Requires full correlation with clinical assessment and confirmatory testing.",
            }
        ],
        "care_pathway": "Clinical triage based on symptoms, vitals, oxygenation, and comorbid risk profile.",
    }


def _red_flags() -> list[str]:
    return [
        "Increasing breathlessness or difficulty speaking full sentences.",
        "Persistent oxygen desaturation or cyanosis.",
        "Chest pain, confusion, drowsiness, or hemodynamic instability.",
        "High fever with worsening cough or inability to maintain hydration.",
    ]


def build_report(
    predicted_label: str,
    probabilities: list[float] | np.ndarray,
    gradcam: np.ndarray,
    patient_name: str | None = None,
    patient_id: str | None = None,
    hospital_name: str = "PulmoVision AI",
    labels: list[str] | None = None,
) -> dict:
    """Create structured doctor-style report content."""
    if not predicted_label:
        raise ValueError("predicted_label is required")

    labels = labels or ["COVID", "Pneumonia", "Normal"]
    confidence = _normalize_probabilities(probabilities, labels)
    severity, mean_intensity = calculate_severity(gradcam)

    med_info = _medication_guidance(predicted_label)
    findings = (
        f"AI model prediction favors '{predicted_label}' with Grad-CAM mean intensity {mean_intensity:.2f}, "
        f"suggesting {severity.lower()} radiographic involvement in highlighted lung regions."
    )

    report_lines = [
        f"{hospital_name}",
        "AI-Assisted Clinical Report (Lung Imaging)",
        f"Date/Time (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "Patient Details",
        f"- Name: {patient_name or 'Not Provided'}",
        f"- ID: {patient_id or 'Not Provided'}",
        "",
        "Diagnosis",
        f"- Predicted Label: {predicted_label}",
        f"- Severity Level: {severity}",
        "",
        "Prediction Confidence",
        *[f"- {name}: {score * 100:.2f}%" for name, score in confidence.items()],
        "",
        "Findings",
        f"- {findings}",
        "",
        "Medication Classes (Non-Prescriptive)",
    ]

    for item in med_info["classes"]:
        report_lines.append(f"- Class: {item['class']}")
        report_lines.append(f"  • Generic examples: {', '.join(item['examples'])}")
        report_lines.append(f"  • Typical consideration: {item['indication']}")

    report_lines.extend(
        [
            "",
            "Care Pathway",
            f"- {med_info['care_pathway']}",
            "",
            "Red Flags (Urgent Care)",
            *[f"- {rf}" for rf in _red_flags()],
            "",
            "Disclaimer",
            DISCLAIMER,
        ]
    )

    return {
        "hospital_name": hospital_name,
        "timestamp_utc": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "patient_name": patient_name or "Not Provided",
        "patient_id": patient_id or "Not Provided",
        "predicted_label": predicted_label,
        "severity": severity,
        "mean_intensity": mean_intensity,
        "confidence": confidence,
        "findings": findings,
        "medication_guidance": med_info,
        "red_flags": _red_flags(),
        "disclaimer": DISCLAIMER,
        "report_text": "\n".join(report_lines),
    }


def export_pdf(report: dict) -> bytes:
    """Export report dictionary to clean PDF bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Title"], fontSize=18, textColor=colors.darkblue)
    section_style = ParagraphStyle("Section", parent=styles["Heading2"], fontSize=12, textColor=colors.darkred)
    body_style = styles["BodyText"]

    elements = [
        Paragraph(report.get("hospital_name", "PulmoVision AI"), title_style),
        Paragraph("[Logo Placeholder]", body_style),
        Spacer(1, 10),
        Paragraph("AI-Assisted Clinical Report", section_style),
        Spacer(1, 10),
    ]

    info_table = Table(
        [
            ["Patient Name", report.get("patient_name", "-")],
            ["Patient ID", report.get("patient_id", "-")],
            ["Timestamp", report.get("timestamp_utc", "-")],
            ["Predicted Label", report.get("predicted_label", "-")],
            ["Severity", report.get("severity", "-")],
        ],
        colWidths=[140, 360],
    )
    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    elements.extend([info_table, Spacer(1, 10)])

    elements.append(Paragraph("Findings", section_style))
    elements.append(Paragraph(report.get("findings", "-"), body_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("Prediction Confidence", section_style))
    for label, score in report.get("confidence", {}).items():
        elements.append(Paragraph(f"- {label}: {score * 100:.2f}%", body_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("Medication Classes (Non-Prescriptive)", section_style))
    for item in report.get("medication_guidance", {}).get("classes", []):
        elements.append(Paragraph(f"- Class: {item['class']}", body_style))
        elements.append(Paragraph(f"&nbsp;&nbsp;Generic examples: {', '.join(item['examples'])}", body_style))
        elements.append(Paragraph(f"&nbsp;&nbsp;Typical consideration: {item['indication']}", body_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("Care Pathway", section_style))
    elements.append(Paragraph(report.get("medication_guidance", {}).get("care_pathway", "-"), body_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("Red Flags", section_style))
    for red_flag in report.get("red_flags", []):
        elements.append(Paragraph(f"- {red_flag}", body_style))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Disclaimer", section_style))
    elements.append(Paragraph(report.get("disclaimer", DISCLAIMER), body_style))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def run_streamlit_app() -> None:
    st.set_page_config(page_title="PulmoVision AI Clinical Report", layout="wide")
    st.title("PulmoVision AI - Clinical Report Generator")
    st.caption("AI-assisted, non-prescriptive report generation for lung disease classification outputs.")

    patient_name = st.text_input("Patient Name (optional)")
    patient_id = st.text_input("Patient ID (optional)")
    predicted_label = st.selectbox("Predicted Label", ["COVID", "Pneumonia", "Normal"])

    st.subheader("Model Scores")
    s1, s2, s3 = st.columns(3)
    covid = s1.slider("COVID score", 0.0, 1.0, 0.3, 0.01)
    pneumonia = s2.slider("Pneumonia score", 0.0, 1.0, 0.4, 0.01)
    normal = s3.slider("Normal score", 0.0, 1.0, 0.3, 0.01)

    st.subheader("Grad-CAM Input")
    mode = st.radio("Select heatmap source", ["Demo random heatmap", "Upload .npy heatmap"], horizontal=True)
    if mode == "Upload .npy heatmap":
        uploaded = st.file_uploader("Upload Grad-CAM array (.npy)", type=["npy"])
        gradcam = np.load(uploaded) if uploaded is not None else None
    else:
        gradcam = np.random.rand(224, 224).astype(np.float32)
        st.info("Using random demo Grad-CAM heatmap (224x224).")

    if st.button("Generate Report"):
        if gradcam is None:
            st.error("Please upload a valid Grad-CAM .npy file or use demo heatmap.")
            return

        report = build_report(
            predicted_label=predicted_label,
            probabilities=[covid, pneumonia, normal],
            gradcam=gradcam,
            patient_name=patient_name or None,
            patient_id=patient_id or None,
            labels=["COVID", "Pneumonia", "Normal"],
        )

        st.success("Report generated.")
        st.text(report["report_text"])

        pdf = export_pdf(report)
        st.download_button(
            label="Download PDF",
            data=pdf,
            file_name="pulmovision_clinical_report.pdf",
            mime="application/pdf",
        )


if __name__ == "__main__":
    run_streamlit_app()
