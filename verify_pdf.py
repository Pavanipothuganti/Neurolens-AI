import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.app.reports import generate_report_pdf
import json

# Mock analysis data
analysis = {
    "id": 1,
    "filename": "test_mri.jpg",
    "created_at": "2024-04-01 12:00:00",
    "label": "MILD IMPAIRMENT",
    "confidence": 0.85,
    "classes": ["No Impairment", "Very Mild Impairment", "Mild Impairment", "Moderate Impairment"],
    "probabilities": [0.05, 0.10, 0.85, 0.00],
    "image_bytes": open("/home/pavani_pothuganti/Desktop/Major Project/41598_2023_41576_Fig1_HTML.jpg", "rb").read()
}

try:
    pdf_bytes = generate_report_pdf(analysis, explanation_base64=None)
    with open("/tmp/test_report.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("PDF generation successful!")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
