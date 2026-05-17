"""
Face Verifier — DeepFace-powered face matching + basic liveness heuristic.

Feature #1 from the implementation guide.
"""
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Lazy import so the server starts even without deepface installed
try:
    from deepface import DeepFace
    _DEEPFACE_AVAILABLE = True
except ImportError:
    _DEEPFACE_AVAILABLE = False
    logger.warning("DeepFace not installed — face verification will return stub results.")


class FaceVerifier:
    """
    Compare face in an ID document against a live selfie.

    Uses an ensemble of three DeepFace models for robustness.
    Falls back gracefully when DeepFace / TF are not installed.
    """

    MODELS          = ["VGG-Face", "Facenet", "ArcFace"]
    MATCH_THRESHOLD = 0.6   # distance < threshold → match
    LIVE_CONF_MIN   = 0.80  # DeepFace face-confidence to call 'live'

    # ── Public API ─────────────────────────────────────────────────────────

    def verify_face_match(self, doc_image: np.ndarray, selfie_image: np.ndarray) -> dict:
        """
        Compare doc photo vs selfie.

        Returns
        -------
        {
            face_match:       bool,
            match_confidence: 0-100,
            distance:         float (lower = closer match),
            is_live:          bool,
            model_used:       list[str],
            error:            str | None,
        }
        """
        if not _DEEPFACE_AVAILABLE:
            return self._stub("DeepFace not installed")

        try:
            doc_face    = self._extract_face(doc_image)
            selfie_face = self._extract_face(selfie_image)

            if doc_face is None or selfie_face is None:
                return self._fail("Could not detect face in one or both images")

            distances, models_used = [], []
            for model in self.MODELS:
                try:
                    result = DeepFace.verify(
                        img1_path=doc_face,
                        img2_path=selfie_face,
                        model_name=model,
                        enforce_detection=False,
                        silent=True,
                    )
                    distances.append(result["distance"])
                    models_used.append(model)
                except Exception:
                    continue

            if not distances:
                return self._fail("All face models failed to compare images")

            avg_dist    = float(np.mean(distances))
            is_match    = avg_dist < self.MATCH_THRESHOLD
            confidence  = max(0, int((1 - avg_dist) * 100))
            is_live     = self._check_liveness(selfie_image)

            return {
                "face_match":       is_match,
                "match_confidence": confidence,
                "distance":         round(avg_dist, 4),
                "is_live":          is_live,
                "model_used":       models_used,
                "error":            None,
            }

        except Exception as exc:
            logger.error("Face verification error: %s", exc)
            return self._fail(str(exc))

    # ── Private helpers ────────────────────────────────────────────────────

    def _extract_face(self, image: np.ndarray):
        """Extract highest-confidence face crop; returns ndarray or None."""
        try:
            faces = DeepFace.extract_faces(image, enforce_detection=True, silent=True)
            if not faces:
                return None
            best = max(faces, key=lambda f: f.get("confidence", 0))
            face_arr = (best["face"] * 255).astype(np.uint8)
            return face_arr
        except Exception:
            return None

    def _check_liveness(self, image: np.ndarray) -> bool:
        """
        Heuristic liveness: if DeepFace detects a face with confidence ≥ threshold
        the image is considered 'live'.  (Real anti-spoofing would use a dedicated
        model such as Silent-Face or FaceBoxes-AntiSpoof.)
        """
        try:
            faces = DeepFace.extract_faces(image, enforce_detection=True, silent=True)
            if not faces:
                return False
            return max(f.get("confidence", 0) for f in faces) >= self.LIVE_CONF_MIN
        except Exception:
            return False

    # ── Stub / failure helpers ─────────────────────────────────────────────

    @staticmethod
    def _fail(msg: str) -> dict:
        return {
            "face_match": False, "match_confidence": 0,
            "distance": 1.0,     "is_live": False,
            "model_used": [],    "error": msg,
        }

    @staticmethod
    def _stub(msg: str) -> dict:
        """Return a neutral stub when DeepFace is unavailable."""
        return {
            "face_match": None, "match_confidence": None,
            "distance": None,   "is_live": None,
            "model_used": [],   "error": msg,
        }


# Module-level singleton — imported by routes
face_verifier = FaceVerifier()
