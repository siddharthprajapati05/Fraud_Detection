"""
DocVerify AI — FastAPI backend.

All four features from the implementation guide are wired here:
  1. /api/verify            – standard OCR + ELA fraud + ML classifier + confidence
  2. /api/verify-with-face  – all of the above + face liveness check
  3. /api/health            – health probe for CI / k8s
"""
from __future__ import annotations

import io
import time
import uuid
import logging

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# ── Domain models ─────────────────────────────────────────────────────────────
from models.ocr_processor       import extract_ocr
from models.fraud_detector      import detect_fraud_ela
from models.face_verifier       import face_verifier
from models.confidence_calculator import confidence_calculator
from models.document_classifier import DocumentClassifier

# ── App init ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DocVerify AI",
    description="KYC document verification with ELA fraud detection, OCR, "
                "face liveness, and ML classification.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load ML classifier once at startup (heavy model)
classifier = DocumentClassifier()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _read_image(file_bytes: bytes) -> np.ndarray:
    """Decode raw bytes → OpenCV BGR image.  Raises HTTPException on failure."""
    arr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=422, detail="Could not decode image file.")
    return img


def _kyc_verdict(fraud_result: dict, ocr_result: dict, ml_result: dict,
                 face_result: dict | None = None) -> str:
    """
    Combine all signals into a final KYC verdict.
    APPROVED only when every mandatory check is clean.
    """
    fraud_ok = fraud_result["fraud_score"] < 50
    ocr_ok   = ocr_result["confidence"]    > 30
    ml_ok    = ml_result.get("prediction") in (None, "genuine")

    face_ok  = True   # default when face check not run
    if face_result and face_result.get("face_match") is not None:
        face_ok = face_result["face_match"] and bool(face_result.get("is_live"))

    return "APPROVED" if all([fraud_ok, ocr_ok, ml_ok, face_ok]) else "REJECTED"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    """Quick health probe."""
    return {"status": "ok", "service": "DocVerify AI", "version": "2.0.0"}


@app.post("/api/verify")
async def verify_document(file: UploadFile = File(...)):
    """
    Standard document verification pipeline.

    Runs: OCR → ELA fraud detection → ML classification → confidence scoring.
    """
    start = time.time()
    session_id = str(uuid.uuid4())[:8]

    try:
        contents = await file.read()
        image    = _read_image(contents)

        # ── Core checks ────────────────────────────────────────────────────
        ocr_result   = extract_ocr(image)
        fraud_result = detect_fraud_ela(image)
        ml_result    = classifier.predict(image)
        conf_data    = confidence_calculator.calculate_verification_confidence(
                           ocr_result, fraud_result, face_result=None)

        return {
            "session_id":    session_id,
            "status":        "completed",

            # OCR
            "extracted_fields": ocr_result["fields"],
            "extracted_text":   ocr_result["text"],
            "ocr_confidence":   ocr_result["confidence"],
            "document_type":    ocr_result["document_type"],
            "word_count":       ocr_result["word_count"],

            # Fraud
            "fraud_score":        fraud_result["fraud_score"],
            "tampering_detected": fraud_result["tampering_detected"],
            "tampering_regions":  fraud_result["regions"],
            "ela_mean":           fraud_result["ela_mean"],
            "risk_label":         fraud_result["risk_label"],

            # ML
            "ml_classification": ml_result,

            # Confidence explainability
            "checks":            conf_data["checks"],
            "overall_risk_score":conf_data["overall_score"],
            "risk_level":        conf_data["risk_level"],
            "recommendation":    conf_data["recommendation"],
            "failed_checks":     conf_data["failed_checks"],

            # Final verdict
            "kyc_status":        _kyc_verdict(fraud_result, ocr_result, ml_result),

            "processing_time":   round(time.time() - start, 2),
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unhandled error in /api/verify")
        return {"status": "error", "message": str(exc), "session_id": session_id}


@app.post("/api/verify-with-face")
async def verify_with_face(
    document_file: UploadFile = File(...),
    selfie_file:   UploadFile = File(...),
):
    """
    Full KYC pipeline: document verification + face liveness check.

    Accepts two uploads:
      - document_file: ID card image (Aadhaar, PAN, Passport, …)
      - selfie_file:   Live selfie of the applicant
    """
    start = time.time()
    session_id = str(uuid.uuid4())[:8]

    try:
        doc_bytes   = await document_file.read()
        self_bytes  = await selfie_file.read()
        doc_image   = _read_image(doc_bytes)
        self_image  = _read_image(self_bytes)

        # ── All checks ─────────────────────────────────────────────────────
        ocr_result   = extract_ocr(doc_image)
        fraud_result = detect_fraud_ela(doc_image)
        ml_result    = classifier.predict(doc_image)
        face_result  = face_verifier.verify_face_match(doc_image, self_image)
        conf_data    = confidence_calculator.calculate_verification_confidence(
                           ocr_result, fraud_result, face_result)

        return {
            "session_id": session_id,
            "status":     "completed",

            # OCR
            "extracted_fields": ocr_result["fields"],
            "extracted_text":   ocr_result["text"],
            "ocr_confidence":   ocr_result["confidence"],
            "document_type":    ocr_result["document_type"],
            "word_count":       ocr_result["word_count"],

            # Fraud
            "fraud_score":        fraud_result["fraud_score"],
            "tampering_detected": fraud_result["tampering_detected"],
            "tampering_regions":  fraud_result["regions"],
            "ela_mean":           fraud_result["ela_mean"],
            "risk_label":         fraud_result["risk_label"],

            # ML
            "ml_classification": ml_result,

            # Face verification
            "face_verification": {
                "face_match":       face_result["face_match"],
                "match_confidence": face_result["match_confidence"],
                "is_live":          face_result["is_live"],
                "distance":         face_result["distance"],
                "model_used":       face_result.get("model_used", []),
                "message": (
                    "Face matches document photo"
                    if face_result.get("face_match")
                    else "Face does NOT match document photo"
                ),
                "error": face_result.get("error"),
            },

            # Confidence explainability
            "checks":            conf_data["checks"],
            "overall_risk_score":conf_data["overall_score"],
            "risk_level":        conf_data["risk_level"],
            "recommendation":    conf_data["recommendation"],
            "failed_checks":     conf_data["failed_checks"],

            # Final verdict
            "kyc_status": _kyc_verdict(fraud_result, ocr_result, ml_result, face_result),

            "processing_time": round(time.time() - start, 2),
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unhandled error in /api/verify-with-face")
        return {"status": "error", "message": str(exc), "session_id": session_id}
