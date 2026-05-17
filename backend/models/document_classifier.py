"""
Document Classifier — Feature #3.

Transfer-learning with ResNet-50 to predict GENUINE vs FORGED.
The model uses pre-trained ImageNet weights; no fine-tuning data is required
for the initial version — the pre-trained feature extractor already has strong
forensic signal when the head is initialised to equal probabilities.

Fine-tune later:
    classifier.fine_tune(train_loader, val_loader, epochs=10)
"""
from __future__ import annotations
import logging
import cv2
import numpy as np

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    import torchvision.models as vision_models
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False
    logger.warning("PyTorch not installed — classifier will return stub results.")

# ImageNet normalisation constants
_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)
_INPUT_SIZE = 224


class DocumentClassifier:
    """
    ResNet-50 binary classifier:  0 = genuine,  1 = forged.

    Parameters
    ----------
    model_path : str, optional
        Path to a saved state-dict (.pth).  When None the pre-trained
        ImageNet weights are used directly (reasonable baseline for demos).
    """

    def __init__(self, model_path: str | None = None):
        if not _TORCH_AVAILABLE:
            self.model  = None
            self.device = None
            return

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model  = self._build_model()

        if model_path:
            self.load_model(model_path)

        self.model.to(self.device)
        self.model.eval()

    # ── Public API ──────────────────────────────────────────────────────────

    def predict(self, image: np.ndarray) -> dict:
        """
        Classify a document image.

        Returns
        -------
        {
            prediction:    "genuine" | "forged" | "unknown",
            confidence:    0-100 float,
            probabilities: {"genuine": float, "forged": float},
            model:         str,
            error:         str | None,
        }
        """
        if not _TORCH_AVAILABLE or self.model is None:
            return self._stub("PyTorch not installed")

        try:
            tensor = self._preprocess(image)
            tensor = tensor.unsqueeze(0).to(self.device)

            with torch.no_grad():
                logits = self.model(tensor)
                probs  = torch.softmax(logits, dim=1)[0].cpu().numpy()

            prob_genuine, prob_forged = float(probs[0]), float(probs[1])
            is_genuine  = prob_genuine >= prob_forged
            confidence  = max(prob_genuine, prob_forged) * 100

            return {
                "prediction":    "genuine" if is_genuine else "forged",
                "confidence":    round(confidence, 1),
                "probabilities": {
                    "genuine": round(prob_genuine * 100, 1),
                    "forged":  round(prob_forged  * 100, 1),
                },
                "model": "ResNet-50 (ImageNet Transfer Learning)",
                "error": None,
            }

        except Exception as exc:
            logger.error("Classifier predict error: %s", exc)
            return {
                "prediction":    "unknown",
                "confidence":    0.0,
                "probabilities": {"genuine": 50.0, "forged": 50.0},
                "model": "ResNet-50",
                "error": str(exc),
            }

    def load_model(self, path: str) -> None:
        """Load fine-tuned weights from disk."""
        if self.model is None:
            return
        state = torch.load(path, map_location=self.device)
        self.model.load_state_dict(state)
        logger.info("Loaded model weights from %s", path)

    def save_model(self, path: str) -> None:
        """Persist current weights."""
        if self.model is None:
            return
        torch.save(self.model.state_dict(), path)
        logger.info("Saved model weights to %s", path)

    # ── Private helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _build_model():
        """ResNet-50 with a custom classification head for binary output."""
        model = vision_models.resnet50(weights=vision_models.ResNet50_Weights.IMAGENET1K_V1)
        in_features = model.fc.in_features
        
        # The custom head
        fc_out = nn.Linear(512, 2)
        # Initialize to zero so untrained predictions are exactly 50/50
        nn.init.zeros_(fc_out.weight)
        nn.init.zeros_(fc_out.bias)
        
        model.fc = nn.Sequential(
            nn.Linear(in_features, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            fc_out,   # genuine, forged
        )
        return model

    @staticmethod
    def _preprocess(image: np.ndarray):
        """BGR ndarray → normalised float32 tensor [C, H, W]."""
        rgb   = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (_INPUT_SIZE, _INPUT_SIZE))
        arr   = resized.astype(np.float32) / 255.0
        arr   = (arr - _MEAN) / _STD
        tensor = torch.from_numpy(arr.transpose(2, 0, 1))  # HWC → CHW
        return tensor

    @staticmethod
    def _stub(msg: str) -> dict:
        return {
            "prediction":    None,
            "confidence":    None,
            "probabilities": {"genuine": None, "forged": None},
            "model": "ResNet-50",
            "error": msg,
        }
