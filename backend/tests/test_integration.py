"""
Integration tests — Feature #4.

Uses FastAPI's TestClient to hit real endpoints and validate the full pipeline.
DeepFace / PyTorch calls are mocked so the suite runs without GPU.
"""
import io
import numpy as np
import pytest
import cv2
from PIL import Image
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ── App import (after patching heavy deps) ────────────────────────────────────
# We patch before importing app to avoid loading TF/PyTorch at import time
with patch("models.document_classifier._TORCH_AVAILABLE", False), \
     patch("models.face_verifier._DEEPFACE_AVAILABLE", False):
    from app import app

client = TestClient(app)


# ── Image factory ─────────────────────────────────────────────────────────────

def _make_jpeg_bytes(text_label: str = "TEST") -> bytes:
    """Create an in-memory JPEG from a white image with a text label."""
    h, w = 400, 600
    img  = np.full((h, w, 3), 240, dtype=np.uint8)
    cv2.putText(img, text_label, (30, 200),
                cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 0), 4)
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


# ── Health ─────────────────────────────────────────────────────────────────────

class TestHealthEndpoint:

    def test_health_ok(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_health_has_version(self):
        data = client.get("/api/health").json()
        assert "version" in data


# ── /api/verify ───────────────────────────────────────────────────────────────

class TestVerifyEndpoint:

    def test_valid_image_returns_completed(self):
        files    = {"file": ("test.jpg", _make_jpeg_bytes(), "image/jpeg")}
        response = client.post("/api/verify", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "completed"

    def test_response_has_all_keys(self):
        files = {"file": ("test.jpg", _make_jpeg_bytes(), "image/jpeg")}
        data  = client.post("/api/verify", files=files).json()

        required = [
            "session_id", "status", "extracted_fields", "ocr_confidence",
            "fraud_score", "tampering_detected", "ml_classification",
            "checks", "overall_risk_score", "risk_level",
            "recommendation", "kyc_status", "processing_time",
        ]
        for key in required:
            assert key in data, f"Missing key: {key}"

    def test_session_id_is_8_chars(self):
        files = {"file": ("test.jpg", _make_jpeg_bytes(), "image/jpeg")}
        data  = client.post("/api/verify", files=files).json()
        assert len(data["session_id"]) == 8

    def test_fraud_score_in_range(self):
        files = {"file": ("test.jpg", _make_jpeg_bytes(), "image/jpeg")}
        data  = client.post("/api/verify", files=files).json()
        assert 0 <= data["fraud_score"] <= 100

    def test_invalid_file_returns_error(self):
        files    = {"file": ("bad.txt", b"not an image at all", "text/plain")}
        response = client.post("/api/verify", files=files)
        # Either 422 or a JSON error message
        if response.status_code == 200:
            assert response.json().get("status") == "error"
        else:
            assert response.status_code in (400, 422)

    def test_risk_level_valid(self):
        files = {"file": ("test.jpg", _make_jpeg_bytes(), "image/jpeg")}
        data  = client.post("/api/verify", files=files).json()
        assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH")

    def test_kyc_status_valid(self):
        files = {"file": ("test.jpg", _make_jpeg_bytes(), "image/jpeg")}
        data  = client.post("/api/verify", files=files).json()
        assert data["kyc_status"] in ("APPROVED", "REJECTED")

    def test_checks_list_structure(self):
        files  = {"file": ("test.jpg", _make_jpeg_bytes(), "image/jpeg")}
        data   = client.post("/api/verify", files=files).json()
        checks = data.get("checks", [])
        assert isinstance(checks, list)
        assert len(checks) >= 4
        for c in checks:
            assert "name" in c and "score" in c and "status" in c


# ── /api/verify-with-face ────────────────────────────────────────────────────

class TestVerifyWithFaceEndpoint:

    def _post(self):
        doc_bytes  = _make_jpeg_bytes("DOC")
        self_bytes = _make_jpeg_bytes("SELFIE")
        files = {
            "document_file": ("doc.jpg",    doc_bytes,  "image/jpeg"),
            "selfie_file":   ("selfie.jpg", self_bytes, "image/jpeg"),
        }
        return client.post("/api/verify-with-face", files=files)

    def test_returns_200(self):
        assert self._post().status_code == 200

    def test_response_has_face_verification(self):
        data = self._post().json()
        assert "face_verification" in data

    def test_face_verification_keys(self):
        fv = self._post().json()["face_verification"]
        for k in ("face_match", "match_confidence", "is_live", "message"):
            assert k in fv

    def test_kyc_status_present(self):
        data = self._post().json()
        assert "kyc_status" in data
        assert data["kyc_status"] in ("APPROVED", "REJECTED")
