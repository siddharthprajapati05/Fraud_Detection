"""
Tests for face verification — Feature #4.

These tests exercise the FaceVerifier logic without needing real photos.
DeepFace calls are mocked out so the suite runs in CI without GPU or TF.
"""
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from models.face_verifier import FaceVerifier


def _blank_face_image(size=(224, 224)) -> np.ndarray:
    return np.zeros((*size, 3), dtype=np.uint8)


class TestFaceVerifier:

    def test_stub_when_deepface_unavailable(self):
        """
        When DeepFace is not installed the verifier should return a stub
        with error set and face_match == None.
        """
        verifier = FaceVerifier()
        # Simulate missing DeepFace by patching the module flag
        with patch("models.face_verifier._DEEPFACE_AVAILABLE", False):
            result = verifier.verify_face_match(
                _blank_face_image(), _blank_face_image()
            )
        assert result["face_match"] is None
        assert result["error"] is not None

    def test_returns_required_keys(self):
        """verify_face_match always returns all expected keys."""
        verifier = FaceVerifier()
        with patch("models.face_verifier._DEEPFACE_AVAILABLE", False):
            result = verifier.verify_face_match(
                _blank_face_image(), _blank_face_image()
            )
        for key in ("face_match", "match_confidence", "distance",
                    "is_live", "model_used", "error"):
            assert key in result

    def test_no_face_detected(self):
        """
        When _extract_face returns None the verifier should short-circuit
        and return face_match=False with an appropriate error.
        """
        verifier = FaceVerifier()
        with patch("models.face_verifier._DEEPFACE_AVAILABLE", True):
            with patch.object(verifier, "_extract_face", return_value=None):
                result = verifier.verify_face_match(
                    _blank_face_image(), _blank_face_image()
                )
        assert result["face_match"] is False
        assert "Could not detect face" in result["error"]

    def test_matching_faces_mock(self):
        """Mock DeepFace.verify to return a low distance → face_match = True."""
        verifier    = FaceVerifier()
        mock_face   = np.ones((96, 96, 3), dtype=np.float32) * 0.5  # float 0-1
        mock_result = {"distance": 0.25, "verified": True}

        with patch("models.face_verifier._DEEPFACE_AVAILABLE", True):
            with patch.object(verifier, "_extract_face", return_value=mock_face):
                with patch("models.face_verifier.DeepFace") as mock_df:
                    mock_df.verify.return_value  = mock_result
                    mock_df.extract_faces.return_value = [
                        {"face": mock_face, "confidence": 0.95}
                    ]
                    result = verifier.verify_face_match(
                        _blank_face_image(), _blank_face_image()
                    )

        assert result["face_match"] is True
        assert result["match_confidence"] > 50

    def test_non_matching_faces_mock(self):
        """Mock a large distance → face_match = False."""
        verifier    = FaceVerifier()
        mock_face   = np.ones((96, 96, 3), dtype=np.float32) * 0.5

        with patch("models.face_verifier._DEEPFACE_AVAILABLE", True):
            with patch.object(verifier, "_extract_face", return_value=mock_face):
                with patch("models.face_verifier.DeepFace") as mock_df:
                    mock_df.verify.return_value = {"distance": 0.85, "verified": False}
                    mock_df.extract_faces.return_value = [
                        {"face": mock_face, "confidence": 0.90}
                    ]
                    result = verifier.verify_face_match(
                        _blank_face_image(), _blank_face_image()
                    )

        assert result["face_match"] is False

    def test_liveness_low_confidence(self):
        """When face confidence < 0.80 liveness should be False."""
        verifier  = FaceVerifier()
        mock_face = np.ones((96, 96, 3), dtype=np.float32) * 0.5

        with patch("models.face_verifier._DEEPFACE_AVAILABLE", True):
            with patch("models.face_verifier.DeepFace") as mock_df:
                mock_df.extract_faces.return_value = [
                    {"face": mock_face, "confidence": 0.50}
                ]
                is_live = verifier._check_liveness(_blank_face_image())

        assert is_live is False
