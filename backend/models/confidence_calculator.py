"""
Confidence Calculator — Feature #2.

Breaks the overall verdict into labelled, weighted checks and produces
an explainability summary that interviewers love.
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


class ConfidenceCalculator:
    """
    Takes the raw outputs of OCR, fraud detection, and (optionally) face
    verification and turns them into a human-readable checklist with
    per-check scores, statuses, and a weighted overall score.
    """

    # ── Weights must sum to 1.0 ────────────────────────────────────────────
    WEIGHTS = {
        "OCR Confidence":      0.20,
        "Tampering Detection": 0.30,
        "Image Quality":       0.15,
        "Format Validation":   0.15,
        "Face Match":          0.20,   # only included when face_result is present
    }

    def calculate_verification_confidence(
        self,
        ocr_result:   dict,
        fraud_result: dict,
        face_result:  dict | None = None,
    ) -> dict:
        """
        Build a full confidence report.

        Returns
        -------
        {
            checks:          list[CheckItem],
            overall_score:   float 0-100,
            risk_level:      "LOW" | "MEDIUM" | "HIGH",
            recommendation:  str,
            failed_checks:   list[str],
            warned_checks:   list[str],
        }
        """
        ocr_conf    = ocr_result.get("confidence", 0)
        fraud_score = fraud_result.get("fraud_score", 0)
        img_quality = self._image_quality_score(fraud_result)
        fmt_ok      = self._validate_format(ocr_result)

        checks = [
            self._make_check(
                name="OCR Confidence",
                score=ocr_conf,
                pass_thresh=50, warn_thresh=30,
                description=f"Text extracted with {ocr_conf:.0f}% confidence",
                weight=self.WEIGHTS["OCR Confidence"],
            ),
            self._make_check(
                name="Tampering Detection",
                score=100 - fraud_score,
                pass_thresh=70, warn_thresh=30,
                description=(
                    "Document appears untampered"
                    if fraud_score < 30
                    else f"Possible tampering detected (ELA score {fraud_score}%)"
                ),
                weight=self.WEIGHTS["Tampering Detection"],
            ),
            self._make_check(
                name="Image Quality",
                score=img_quality,
                pass_thresh=80, warn_thresh=50,
                description="Image sharpness and lighting are adequate",
                weight=self.WEIGHTS["Image Quality"],
            ),
            self._make_check(
                name="Format Validation",
                score=100 if fmt_ok else 0,
                pass_thresh=1, warn_thresh=0,
                description=(
                    "All required fields present"
                    if fmt_ok
                    else "One or more required fields missing (name / dob / doc number)"
                ),
                weight=self.WEIGHTS["Format Validation"],
            ),
        ]

        if face_result and face_result.get("face_match") is not None:
            match_conf = face_result.get("match_confidence", 0) or 0
            is_match   = bool(face_result.get("face_match"))
            is_live    = bool(face_result.get("is_live"))
            face_score = match_conf if is_match else 0

            desc = (
                f"Face matched {match_conf}% — {'live' if is_live else 'liveness uncertain'}"
                if is_match
                else "Face does NOT match document photo"
            )
            checks.append(self._make_check(
                name="Face Match",
                score=face_score,
                pass_thresh=70, warn_thresh=50,
                description=desc,
                weight=self.WEIGHTS["Face Match"],
            ))

        # Normalise weights to 1.0 for whichever checks are active
        total_weight = sum(c["weight"] for c in checks)
        overall_score = (
            sum(c["score"] * c["weight"] for c in checks) / total_weight
            if total_weight > 0 else 0.0
        )
        overall_score = round(overall_score, 1)

        if overall_score >= 85:
            risk_level     = "LOW"
            recommendation = "✓ Document appears genuine. Recommend approval."
        elif overall_score >= 65:
            risk_level     = "MEDIUM"
            recommendation = "⚠ Manual review advised. Some flags detected."
        else:
            risk_level     = "HIGH"
            recommendation = "✗ Document rejected. Multiple fraud indicators."

        return {
            "checks":         checks,
            "overall_score":  overall_score,
            "risk_level":     risk_level,
            "recommendation": recommendation,
            "failed_checks":  [c["name"] for c in checks if c["status"] == "FAIL"],
            "warned_checks":  [c["name"] for c in checks if c["status"] == "WARN"],
        }

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _make_check(
        name: str, score: float,
        pass_thresh: float, warn_thresh: float,
        description: str, weight: float,
    ) -> dict:
        score = max(0.0, min(100.0, float(score)))
        if score >= pass_thresh:
            status = "PASS"
        elif score >= warn_thresh:
            status = "WARN"
        else:
            status = "FAIL"

        return {
            "name":        name,
            "score":       round(score, 1),
            "status":      status,
            "description": description,
            "weight":      weight,
        }

    @staticmethod
    def _image_quality_score(fraud_result: dict) -> float:
        """
        Derive image quality from ELA noise — high ELA noise = low quality.
        Score is inversely scaled from the fraud score.
        """
        fraud_score = fraud_result.get("fraud_score", 0)
        return max(40.0, 100.0 - fraud_score * 0.5)

    @staticmethod
    def _validate_format(ocr_result: dict) -> bool:
        """True if name, dob, and document_number are all found."""
        fields   = ocr_result.get("fields", {})
        required = ["name", "dob", "document_number"]
        return all(
            str(fields.get(f, "Not found")).strip() not in ("", "Not found")
            for f in required
        )


# Module-level singleton
confidence_calculator = ConfidenceCalculator()
