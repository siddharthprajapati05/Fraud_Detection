"""
OCR Processor — extracts text and structured fields from document images.
Uses Tesseract under the hood with preprocessing for maximum accuracy.
"""
import re
import cv2
import numpy as np
import pytesseract
import logging

logger = logging.getLogger(__name__)

# ─── Regex patterns for Indian government IDs ────────────────────────────────
PATTERNS = {
    "aadhaar":       r"\b\d{4}\s\d{4}\s\d{4}\b",
    "pan":           r"\b[A-Z]{5}\d{4}[A-Z]\b",
    "dob":           r"\b(\d{2}[\/\-\.]\d{2}[\/\-\.]\d{4}|\d{4}[\/\-\.]\d{2}[\/\-\.]\d{2})\b",
    "name":          r"(?:Name|NAME|Name /|Nane|Nam|Given Name)[:\-\s]+([A-Z][A-Za-z \.]{2,40})",
    "document_number": r"\b(?:\d{4}\s\d{4}\s\d{4}|[A-Z]{5}\d{4}[A-Z]|[A-Z0-9]{8,12})\b",
    "gender":        r"\b(MALE|FEMALE|Male|Female|M|F)\b",
    "address":       r"(?:Address|ADDRESS|S/O|D/O|W/O)[:\s]+(.{10,100})",
    "pincode":       r"\b\d{6}\b",
    "mobile":        r"\b[6-9]\d{9}\b",
    "yob":           r"\bYear of Birth[:\s]+(\d{4})\b",
}


def _preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
    """Enhance image quality before running Tesseract."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Denoise
    gray = cv2.fastNlMeansDenoising(gray, h=10)
    # Adaptive threshold
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2
    )
    # Scale up 2×
    scaled = cv2.resize(thresh, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    return scaled


def _extract_confidence(ocr_data: dict) -> float:
    """Average Tesseract word confidence (ignoring -1 values)."""
    confs = [c for c in ocr_data["conf"] if c != -1]
    return round(float(np.mean(confs)), 1) if confs else 0.0


def _parse_fields(text: str) -> dict:
    """Run regex patterns over raw OCR text and return structured fields."""
    fields: dict = {}

    # Aadhaar
    m = re.search(PATTERNS["aadhaar"], text)
    fields["aadhaar_number"] = m.group() if m else "Not found"

    # PAN
    m = re.search(PATTERNS["pan"], text)
    fields["pan_number"] = m.group() if m else "Not found"

    # DOB
    m = re.search(PATTERNS["dob"], text)
    fields["dob"] = m.group() if m else "Not found"

    # Year of birth (fallback)
    if fields["dob"] == "Not found":
        m = re.search(PATTERNS["yob"], text)
        fields["dob"] = m.group(1) if m else "Not found"

    # Name
    m = re.search(PATTERNS["name"], text, re.IGNORECASE)
    if m:
        # split on newline to ensure we only capture the first line
        fields["name"] = m.group(1).split('\n')[0].strip()
    else:
        fields["name"] = "Not found"

    # Fallback for Name if label wasn't found (common on Indian IDs)
    if fields["name"] == "Not found":
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for i, line in enumerate(lines):
            # If we find DOB, the line(s) before it usually contain the name
            if re.search(PATTERNS["dob"], line) or re.search(PATTERNS["yob"], line):
                if i > 0:
                    prev_line = lines[i-1]
                    # Filter out purely numeric or short garbage lines
                    clean_name = re.sub(r'[^A-Za-z \.]', '', prev_line).strip()
                    if len(clean_name) >= 3 and not "FATHER" in clean_name.upper():
                        fields["name"] = clean_name
                        break
                if i > 1 and fields["name"] == "Not found":
                    # Try two lines above (e.g., PAN card has father's name in between)
                    prev_line = lines[i-2]
                    clean_name = re.sub(r'[^A-Za-z \.]', '', prev_line).strip()
                    if len(clean_name) >= 3 and not "GOVT" in clean_name.upper() and not "TAX" in clean_name.upper():
                        fields["name"] = clean_name
                        break

    # Gender
    m = re.search(PATTERNS["gender"], text)
    fields["gender"] = m.group() if m else "Not found"

    # Pincode
    m = re.search(PATTERNS["pincode"], text)
    fields["pincode"] = m.group() if m else "Not found"

    # Document number (best-effort)
    pan = fields.get("pan_number")
    aadh = fields.get("aadhaar_number")
    fields["document_number"] = aadh if aadh != "Not found" else (pan if pan != "Not found" else "Not found")

    return fields


def detect_document_type(text: str) -> str:
    """Heuristically classify document type from raw text."""
    text_up = text.upper()
    if "AADHAAR" in text_up or "UNIQUE IDENTIFICATION" in text_up:
        return "Aadhaar Card"
    if "INCOME TAX" in text_up or "PERMANENT ACCOUNT" in text_up:
        return "PAN Card"
    if "PASSPORT" in text_up or "REPUBLIC OF INDIA" in text_up:
        return "Passport"
    if "VOTER" in text_up or "ELECTION" in text_up:
        return "Voter ID"
    if "DRIVING" in text_up or "LICENCE" in text_up or "LICENSE" in text_up:
        return "Driving Licence"
    return "Unknown"


def extract_ocr(image: np.ndarray) -> dict:
    """
    Full OCR pipeline.

    Returns
    -------
    {
        "text":          raw string,
        "fields":        structured dict of extracted fields,
        "confidence":    0-100 float,
        "document_type": string,
        "word_count":    int,
    }
    """
    try:
        processed = _preprocess_for_ocr(image)
        config = "--oem 3 --psm 6"
        ocr_data = pytesseract.image_to_data(
            processed, config=config, output_type=pytesseract.Output.DICT
        )
        raw_text = pytesseract.image_to_string(processed, config=config)

        confidence = _extract_confidence(ocr_data)
        fields = _parse_fields(raw_text)
        doc_type = detect_document_type(raw_text)
        word_count = len([w for w in ocr_data["text"] if w.strip()])

        return {
            "text": raw_text.strip(),
            "fields": fields,
            "confidence": confidence,
            "document_type": doc_type,
            "word_count": word_count,
        }

    except Exception as exc:
        logger.error("OCR failed: %s", exc)
        return {
            "text": "",
            "fields": {},
            "confidence": 0.0,
            "document_type": "Unknown",
            "word_count": 0,
        }


# Convenience re-export so `from models.ocr_processor import parse_fields` works in tests
parse_fields = _parse_fields
