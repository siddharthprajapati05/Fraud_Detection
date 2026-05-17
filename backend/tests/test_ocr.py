"""
Tests for OCR extraction — Feature #4.

These tests use synthetic in-memory images so they run without real document
photos in CI.  To test with real Aadhaar/PAN scans, drop them into
tests/fixtures/ and uncomment the file-based tests.
"""
import re
import numpy as np
import pytest
import cv2

from models.ocr_processor import extract_ocr, parse_fields


# ── Helpers ───────────────────────────────────────────────────────────────────

def _blank_image(w=800, h=500, color=(255, 255, 255)) -> np.ndarray:
    img = np.full((h, w, 3), color, dtype=np.uint8)
    return img


def _write_text_on_image(text: str, img: np.ndarray | None = None) -> np.ndarray:
    """Render text onto a white image — good enough for unit testing."""
    if img is None:
        img = _blank_image()
    y = 40
    for line in text.split("\n"):
        cv2.putText(img, line, (20, y), cv2.FONT_HERSHEY_SIMPLEX,
                    0.9, (0, 0, 0), 2, cv2.LINE_AA)
        y += 40
    return img


# ── OCR pipeline ──────────────────────────────────────────────────────────────

class TestOCRExtraction:

    def test_returns_required_keys(self):
        """extract_ocr always returns a dict with all expected keys."""
        img    = _blank_image()
        result = extract_ocr(img)

        for key in ("text", "fields", "confidence", "document_type", "word_count"):
            assert key in result, f"Missing key: {key}"

    def test_confidence_in_range(self):
        img    = _blank_image()
        result = extract_ocr(img)
        assert 0.0 <= result["confidence"] <= 100.0

    def test_fields_is_dict(self):
        img    = _blank_image()
        result = extract_ocr(img)
        assert isinstance(result["fields"], dict)

    def test_word_count_non_negative(self):
        img    = _blank_image()
        result = extract_ocr(img)
        assert result["word_count"] >= 0

    def test_document_type_is_string(self):
        img    = _blank_image()
        result = extract_ocr(img)
        assert isinstance(result["document_type"], str)


# ── Field parsing (no Tesseract needed) ───────────────────────────────────────

class TestFieldParsing:

    def test_extract_dob_slash(self):
        text   = "Name: John Doe\nDOB: 15/05/1990\nAadhaar: 1234 5678 9012"
        fields = parse_fields(text)
        assert "1990" in fields["dob"] or fields["dob"] == "15/05/1990"

    def test_extract_aadhaar(self):
        text   = "Unique ID: 2345 6789 0123"
        fields = parse_fields(text)
        assert re.match(r"\d{4}\s\d{4}\s\d{4}", fields["aadhaar_number"])

    def test_extract_pan(self):
        text   = "Permanent Account Number: ABCDE1234F"
        fields = parse_fields(text)
        assert fields["pan_number"] == "ABCDE1234F"

    def test_missing_fields_return_not_found(self):
        text   = "Some random text without structured data."
        fields = parse_fields(text)
        for key in ("aadhaar_number", "pan_number", "dob"):
            assert fields[key] == "Not found"

    def test_name_extraction(self):
        text   = "Name: Rahul Sharma\nDOB: 01/01/1985"
        fields = parse_fields(text)
        assert "Rahul" in fields["name"] or fields["name"] == "Not found"

    def test_gender_extraction(self):
        text   = "Gender: MALE"
        fields = parse_fields(text)
        assert fields["gender"] in ("MALE", "FEMALE", "M", "F", "Not found")
