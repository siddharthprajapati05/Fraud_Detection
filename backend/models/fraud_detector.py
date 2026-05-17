"""
Fraud Detector — Error Level Analysis (ELA) + heuristic checks.

ELA reveals JPEG re-compression artefacts caused by digital manipulation.
Tampered regions compress differently from the original and appear bright in
the ELA difference image.
"""
import io
import cv2
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────
ELA_QUALITY      = 90          # JPEG quality for ELA re-compression
BRIGHT_THRESHOLD = 50          # pixel brightness → tamper flag
MIN_AREA         = 500         # minimum contour area to count as a region
FRAUD_SCALE      = 0.4         # tuning constant


def _run_ela(image: np.ndarray) -> tuple[np.ndarray, float]:
    """Return (ela_image, mean_brightness)."""
    pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=ELA_QUALITY)
    buf.seek(0)
    recompressed = Image.open(buf).convert("RGB")

    original_arr   = np.array(pil_img,      dtype=np.float32)
    compressed_arr = np.array(recompressed,  dtype=np.float32)

    ela = np.abs(original_arr - compressed_arr)
    ela = np.clip(ela * 15, 0, 255).astype(np.uint8)    # amplify diff

    mean_brightness = float(np.mean(ela))
    return ela, mean_brightness


def _find_tamper_regions(ela_gray: np.ndarray) -> list[dict]:
    """Return bounding boxes of suspicious high-brightness blobs."""
    _, binary = cv2.threshold(ela_gray, BRIGHT_THRESHOLD, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    regions = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area >= MIN_AREA:
            x, y, w, h = cv2.boundingRect(cnt)
            brightness = float(np.mean(ela_gray[y : y + h, x : x + w]))
            regions.append({"x": x, "y": y, "width": w, "height": h,
                            "area": int(area), "brightness": round(brightness, 1)})

    # Sort by brightness descending
    return sorted(regions, key=lambda r: r["brightness"], reverse=True)


def _noise_score(image: np.ndarray) -> float:
    """Estimate noise level via Laplacian variance — higher = noisier."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    lap  = cv2.Laplacian(gray, cv2.CV_64F)
    return float(np.var(lap))


def detect_fraud_ela(image: np.ndarray) -> dict:
    """
    Run full ELA-based fraud pipeline.

    Returns
    -------
    {
        "fraud_score":         0-100,
        "tampering_detected":  bool,
        "regions":             list of region dicts,
        "ela_mean":            float,
        "noise_score":         float,
        "risk_label":          "LOW" | "MEDIUM" | "HIGH",
    }
    """
    try:
        ela_img, ela_mean = _run_ela(image)
        ela_gray          = cv2.cvtColor(ela_img, cv2.COLOR_RGB2GRAY)
        regions           = _find_tamper_regions(ela_gray)
        noise             = _noise_score(image)

        # Raw score driven by ELA brightness + region count
        region_penalty = min(len(regions) * 5, 40)
        brightness_penalty = min(ela_mean * FRAUD_SCALE, 60)
        fraud_score = min(100, int(brightness_penalty + region_penalty))

        return {
            "fraud_score":        fraud_score,
            "tampering_detected": fraud_score > 35,
            "regions":            regions[:10],   # top-10 most suspicious
            "ela_mean":           round(ela_mean, 2),
            "noise_score":        round(noise, 2),
            "risk_label":         "HIGH" if fraud_score > 65 else
                                  "MEDIUM" if fraud_score > 35 else "LOW",
        }

    except Exception as exc:
        logger.error("ELA fraud detection failed: %s", exc)
        return {
            "fraud_score":        0,
            "tampering_detected": False,
            "regions":            [],
            "ela_mean":           0.0,
            "noise_score":        0.0,
            "risk_label":         "LOW",
        }
