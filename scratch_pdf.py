import logging
import sys
from io import BytesIO
from backend.services.report_service import render_html, html_to_pdf
from xhtml2pdf import pisa

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

# Create a mock payload to test the PDF generation
mock_payload = {
    "analysis_id": "test-123",
    "media_type": "image",
    "verdict": {
        "authenticity_score": 30,
        "label": "Likely Fake",
        "severity": "high",
        "model_label": "DeepFakeDetector",
        "model_confidence": 0.99
    },
    "explainability": {
        "exif": {
            "make": "Apple",
            "trust_adjustment": 5
        },
        "vlm_breakdown": {
            "facial_symmetry": {"score": 20, "notes": "Asymmetric"}
        }
    },
    "llm_summary": {
        "paragraph": "This is a test paragraph.",
        "bullets": ["Point 1", "Point 2"],
        "model_used": "gemini"
    }
}

html = render_html(mock_payload)
out_path = "test.pdf"

try:
    with open(out_path, "wb") as f:
        result = pisa.CreatePDF(html, dest=f)
    print(f"PDF creation returned {result.err} errors")
except Exception as e:
    print(f"Exception: {e}")





