import React, { useEffect, useState } from 'react';
import Header       from '../components/Header.jsx';
import UploadWithFace  from '../components/UploadWithFace.jsx';
import ResultsDashboard from '../components/ResultsDashboard.jsx';
import { checkHealth } from '../services/api.js';

const FEATURES = [
  { icon: '🔬', title: 'ELA Fraud Detection',   desc: 'Error Level Analysis reveals JPEG re-compression artefacts from digital tampering.' },
  { icon: '📝', title: 'OCR Extraction',         desc: 'Tesseract-powered text extraction with regex field parsing for Indian IDs.' },
  { icon: '🧬', title: 'Face Liveness Check',    desc: 'Multi-model DeepFace ensemble compares ID photo against live selfie.' },
  { icon: '🤖', title: 'ML Classification',      desc: 'ResNet-50 transfer learning classifies documents as genuine or forged.' },
  { icon: '📊', title: 'Confidence Scoring',     desc: 'Weighted explainability checklist breaks down every verification signal.' },
  { icon: '✅', title: 'KYC Verdict',            desc: 'APPROVED / REJECTED decision synthesised from all checks instantly.' },
];

export default function Dashboard() {
  const [result,    setResult]    = useState(null);
  const [backendOk, setBackendOk] = useState(null);

  // Poll backend health on mount
  useEffect(() => {
    checkHealth()
      .then(d => setBackendOk(d.status === 'ok'))
      .catch(() => setBackendOk(false));
  }, []);

  return (
    <div style={{ minHeight: '100vh' }}>
      <Header backendOk={backendOk} />

      <main className="container" style={{ paddingTop: '3rem', paddingBottom: '5rem' }}>

        {/* ── Hero ─────────────────────────────────────────────────── */}
        {!result && (
          <div className="fade-up" style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
              padding: '0.4rem 1rem',
              borderRadius: '999px',
              background: 'rgba(139,92,246,0.1)',
              border: '1px solid rgba(139,92,246,0.3)',
              fontSize: '0.8rem', fontWeight: 600, color: 'var(--accent-1)',
              marginBottom: '1.5rem', letterSpacing: '0.05em',
            }}>
              🔒 Privacy-first · No external DB · 100% local
            </div>

            <h1>
              AI-Powered <span className="gradient-text">KYC Verification</span>
            </h1>
            <p className="text-secondary" style={{ maxWidth: 560, margin: '1rem auto 0', fontSize: '1.05rem', lineHeight: 1.7 }}>
              Upload an Aadhaar, PAN or Passport — get fraud detection, OCR extraction,
              face liveness analysis and ML classification in seconds.
            </p>
          </div>
        )}

        {/* ── Main Content ─────────────────────────────────────────── */}
        {result ? (
          <ResultsDashboard data={result} onReset={() => setResult(null)} />
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '420px 1fr', gap: '2.5rem', alignItems: 'start' }}>

            {/* Left: upload panel */}
            <div
              className="card fade-up fade-up-d1"
              style={{
                position: 'sticky', top: '90px',
                border: '1px solid var(--border-active)',
                boxShadow: 'var(--shadow-glow)',
              }}
            >
              <h2 style={{ marginBottom: '1.5rem', fontSize: '1.2rem' }}>
                Upload Document
              </h2>
              <UploadWithFace onResult={setResult} />
            </div>

            {/* Right: feature grid */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div
                className="fade-up fade-up-d2"
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(230px, 1fr))',
                  gap: '1rem',
                }}
              >
                {FEATURES.map((f, i) => (
                  <div
                    key={f.title}
                    className="card fade-up"
                    style={{ animationDelay: `${0.1 + i * 0.07}s` }}
                  >
                    <div style={{ fontSize: '1.75rem', marginBottom: '0.75rem' }}>{f.icon}</div>
                    <h3 style={{ fontSize: '0.95rem', marginBottom: '0.4rem' }}>{f.title}</h3>
                    <p className="text-secondary text-sm" style={{ lineHeight: 1.6 }}>{f.desc}</p>
                  </div>
                ))}
              </div>

              {/* Backend status card */}
              <div
                className="card fade-up fade-up-d3"
                style={{
                  padding: '1.25rem 1.5rem',
                  border: backendOk === false ? '1px solid rgba(239,68,68,0.3)' : '1px solid var(--border)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span style={{ fontSize: '1.4rem' }}>
                    {backendOk === null ? '⏳' : backendOk ? '🟢' : '🔴'}
                  </span>
                  <div>
                    <p style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                      {backendOk === null ? 'Checking backend…'
                        : backendOk ? 'Backend API is online'
                        : 'Backend API is offline'}
                    </p>
                    <p className="text-secondary text-xs mt-1">
                      {backendOk
                        ? 'FastAPI server running on localhost:8000 — ready to verify.'
                        : 'Start the backend: cd backend && uvicorn app:app --reload --port 8000'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Quick-start code snippet */}
              <div className="card fade-up" style={{ padding: '1.25rem' }}>
                <p className="text-muted text-xs font-semibold" style={{ textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>
                  Quick Start
                </p>
                <pre
                  className="mono"
                  style={{
                    fontSize: '0.8rem', lineHeight: 1.7, color: 'var(--text-secondary)',
                    background: 'var(--bg-base)', borderRadius: 'var(--radius-sm)',
                    padding: '1rem', overflowX: 'auto', margin: 0,
                  }}
                >
{`# Install & run backend
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --port 8000

# Run tests
pytest tests/ -v --cov=.

# Start frontend (this tab)
cd frontend && npm run dev`}
                </pre>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid var(--border)', padding: '1.5rem 0',
        textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem',
      }}>
        DocVerify AI · ELA Fraud Detection · OCR · DeepFace · ResNet-50 · Privacy-first
      </footer>
    </div>
  );
}
