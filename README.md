# DocVerify AI — KYC Document Verification

> AI-powered KYC pipeline with ELA fraud detection, Tesseract OCR, DeepFace liveness, ResNet-50 ML classification, and a premium React dashboard.

---

## ⚡ Quick Start

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Also install Tesseract (macOS)
brew install tesseract

# Start server
uvicorn app:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## 🗂 Project Structure

```
new/
├── backend/
│   ├── app.py                        ← FastAPI app (all routes)
│   ├── requirements.txt
│   ├── conftest.py                   ← pytest sys.path fix
│   ├── models/
│   │   ├── ocr_processor.py          ← Tesseract OCR + regex fields
│   │   ├── fraud_detector.py         ← ELA tampering detection
│   │   ├── face_verifier.py          ← DeepFace multi-model ensemble
│   │   ├── confidence_calculator.py  ← Weighted explainability scores
│   │   └── document_classifier.py   ← ResNet-50 genuine/forged
│   └── tests/
│       ├── test_ocr.py
│       ├── test_fraud_detection.py
│       ├── test_face_verification.py
│       └── test_integration.py
└── frontend/
    └── src/
        ├── pages/Dashboard.jsx
        ├── components/
        │   ├── Header.jsx
        │   ├── UploadWithFace.jsx       ← drag-drop + mode toggle
        │   ├── ConfidenceChecklist.jsx  ← animated per-check scores
        │   └── ResultsDashboard.jsx     ← full results view
        └── services/api.js
```

---

## 🔌 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET  | `/api/health`            | Health probe |
| POST | `/api/verify`            | Document only (OCR + ELA + ML + Confidence) |
| POST | `/api/verify-with-face`  | + DeepFace face liveness match |

### Example — cURL
```bash
# Document only
curl -X POST http://localhost:8000/api/verify \
  -F "file=@/path/to/aadhaar.jpg"

# With face check
curl -X POST http://localhost:8000/api/verify-with-face \
  -F "document_file=@/path/to/aadhaar.jpg" \
  -F "selfie_file=@/path/to/selfie.jpg"
```

---

## 🧪 Tests

```bash
cd backend
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html
# Open htmlcov/index.html
```

---

## 🚀 Features

| Feature | Tech | Resume Impact |
|---------|------|---------------|
| ELA Fraud Detection | OpenCV + Pillow | ⭐⭐⭐⭐ |
| OCR Extraction | Tesseract + regex | ⭐⭐⭐ |
| Face Liveness Check | DeepFace (VGG-Face, Facenet, ArcFace) | ⭐⭐⭐⭐⭐ |
| ML Classification | ResNet-50 Transfer Learning | ⭐⭐⭐⭐⭐ |
| Confidence Scoring | Weighted explainability | ⭐⭐⭐⭐ |
| Comprehensive Tests | pytest + mocks | ⭐⭐⭐⭐ |

---

## 📦 Dependencies

### Backend
- **FastAPI** + uvicorn
- **OpenCV** + Pillow (image processing)
- **pytesseract** (OCR)
- **DeepFace** + TensorFlow (face verification)
- **PyTorch** + torchvision (ResNet-50 classifier)
- **pytest** + pytest-cov (testing)

### Frontend
- **React 18** + Vite
- **react-dropzone** (drag-and-drop)
- **lucide-react** (icons)
