import React from 'react';
import ConfidenceChecklist from './ConfidenceChecklist.jsx';

/* ── Small helper atoms ──────────────────────────────────────────────── */

function Section({ title, children, delay = 0 }) {
  return (
    <div className="fade-up" style={{ animationDelay: `${delay}s` }}>
      <h3 style={{ fontSize: '0.8rem', fontWeight: 700, letterSpacing: '0.1em',
        textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.85rem' }}>
        {title}
      </h3>
      {children}
    </div>
  );
}

function FieldRow({ label, value }) {
  const missing = !value || value === 'Not found';
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
      padding: '0.6rem 0', borderBottom: '1px solid var(--border)', gap: '1rem',
    }}>
      <span className="text-secondary text-sm">{label}</span>
      <span
        className="mono font-semibold"
        style={{ fontSize: '0.9rem', color: missing ? 'var(--text-muted)' : 'var(--text-primary)',
          textAlign: 'right', maxWidth: '60%', wordBreak: 'break-word' }}
      >
        {missing ? '—' : value}
      </span>
    </div>
  );
}

function StatCard({ label, value, sub, color = 'var(--accent-1)' }) {
  return (
    <div className="card" style={{ textAlign: 'center', padding: '1.25rem 1rem' }}>
      <p className="text-muted text-xs font-semibold" style={{ textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</p>
      <p className="mono font-bold" style={{ fontSize: '1.9rem', color, marginTop: '0.35rem', lineHeight: 1 }}>{value}</p>
      {sub && <p className="text-secondary text-xs mt-1">{sub}</p>}
    </div>
  );
}

function FaceCard({ fv }) {
  if (!fv) return null;
  const matched = fv.face_match;
  const live    = fv.is_live;
  const err     = fv.error;

  if (err && matched === null) {
    return (
      <div style={{ padding: '1rem', borderRadius: 'var(--radius-sm)',
        background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.25)',
        color: 'var(--accent-amber)', fontSize: '0.88rem' }}>
        ⚠ Face check unavailable: {err}
      </div>
    );
  }

  const color  = matched ? 'var(--accent-green)' : 'var(--accent-red)';
  const border = matched ? 'rgba(16,185,129,0.25)' : 'rgba(239,68,68,0.25)';
  const bg     = matched ? 'rgba(16,185,129,0.06)' : 'rgba(239,68,68,0.06)';

  return (
    <div style={{ padding: '1.25rem', borderRadius: 'var(--radius-md)',
      background: bg, border: `1px solid ${border}` }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.85rem' }}>
        <span style={{ fontSize: '2rem' }}>{matched ? '✅' : '❌'}</span>
        <div>
          <p style={{ fontWeight: 700, color, fontSize: '1rem' }}>{fv.message}</p>
          <p className="text-secondary text-xs mt-1">
            Liveness: <strong style={{ color: live ? 'var(--accent-green)' : 'var(--accent-amber)' }}>
              {live === null ? 'N/A' : live ? 'Live person detected' : 'Liveness uncertain'}
            </strong>
          </p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem', marginTop: '0.5rem' }}>
        <div style={{ textAlign: 'center' }}>
          <p className="text-muted text-xs">Confidence</p>
          <p className="mono font-bold" style={{ color, fontSize: '1.3rem' }}>
            {fv.match_confidence ?? 'N/A'}{fv.match_confidence != null && '%'}
          </p>
        </div>
        <div style={{ textAlign: 'center' }}>
          <p className="text-muted text-xs">Distance</p>
          <p className="mono font-bold" style={{ fontSize: '1.3rem' }}>
            {fv.distance != null ? fv.distance.toFixed(3) : 'N/A'}
          </p>
        </div>
        <div style={{ textAlign: 'center' }}>
          <p className="text-muted text-xs">Models</p>
          <p className="mono font-bold" style={{ fontSize: '1rem' }}>
            {fv.model_used?.length ?? 0}
          </p>
        </div>
      </div>
    </div>
  );
}

function MLCard({ ml }) {
  if (!ml) return null;
  if (ml.error || ml.prediction === null) {
    return (
      <div style={{ padding: '0.85rem 1rem', borderRadius: 'var(--radius-sm)',
        background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.25)',
        color: 'var(--accent-amber)', fontSize: '0.88rem' }}>
        ⚠ ML Classifier unavailable: {ml.error}
      </div>
    );
  }
  const isGenuine = ml.prediction === 'genuine';
  const color = isGenuine ? 'var(--accent-green)' : 'var(--accent-red)';

  return (
    <div className="card" style={{ padding: '1rem 1.25rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
        <div>
          <p className="text-secondary text-xs font-semibold" style={{ textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            ML Classification
          </p>
          <p style={{ fontWeight: 700, fontSize: '1.1rem', color, marginTop: '0.2rem' }}>
            {isGenuine ? '✓ Genuine' : '✕ Forged'}
          </p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <p className="text-muted text-xs">Confidence</p>
          <p className="mono font-bold" style={{ fontSize: '1.6rem', color }}>{ml.confidence}%</p>
        </div>
      </div>

      <p className="text-muted text-xs" style={{ marginBottom: '0.4rem' }}>Probability distribution</p>
      <div style={{ display: 'flex', gap: 0, borderRadius: 'var(--radius-sm)', overflow: 'hidden', height: 8 }}>
        <div style={{ width: `${ml.probabilities?.genuine ?? 50}%`, background: 'var(--accent-green)', transition: 'width 0.8s ease' }} />
        <div style={{ flex: 1, background: 'var(--accent-red)' }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.3rem' }}>
        <span className="text-xs text-green">Genuine {ml.probabilities?.genuine}%</span>
        <span className="text-xs text-red">Forged {ml.probabilities?.forged}%</span>
      </div>
      <p className="text-muted text-xs mt-2">{ml.model}</p>
    </div>
  );
}

/* ── Main Results Dashboard ─────────────────────────────────────────── */
export default function ResultsDashboard({ data, onReset }) {
  if (!data) return null;

  const isApproved = data.kyc_status === 'APPROVED';
  const statusColor  = isApproved ? 'var(--accent-green)' : 'var(--accent-red)';
  const statusBorder = isApproved ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)';

  const fields = data.extracted_fields || {};

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>

      {/* ── KYC Verdict Banner ────────────────────────────────────── */}
      <div
        className="card fade-up"
        style={{
          border: `1px solid ${statusBorder}`,
          boxShadow: `0 0 40px ${isApproved ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)'}`,
          padding: '1.5rem 2rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{
              width: 56, height: 56, borderRadius: '50%',
              background: `${statusColor}20`,
              border: `2px solid ${statusColor}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '1.6rem',
            }}>
              {isApproved ? '✓' : '✕'}
            </div>
            <div>
              <p className="text-secondary text-sm">KYC Verdict</p>
              <h2 style={{ color: statusColor, fontSize: '1.8rem', fontWeight: 900 }}>
                {data.kyc_status}
              </h2>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <span className="badge badge-info mono">#{data.session_id}</span>
            <span className="badge badge-info">⏱ {data.processing_time}s</span>
            {data.document_type && <span className="badge badge-info">{data.document_type}</span>}
          </div>
        </div>
      </div>

      {/* ── Stats Row ─────────────────────────────────────────────── */}
      <div className="grid-3 fade-up fade-up-d1">
        <StatCard label="OCR Confidence"     value={`${data.ocr_confidence?.toFixed(0) ?? 0}%`}  color="var(--accent-1)"     sub={`${data.word_count} words`} />
        <StatCard label="Fraud Score"        value={`${data.fraud_score ?? 0}%`}                  color={data.fraud_score > 50 ? 'var(--accent-red)' : 'var(--accent-green)'} sub={data.risk_label} />
        <StatCard label="Overall Risk Score" value={`${data.overall_risk_score ?? 0}%`}           color="var(--accent-3)"     sub={data.risk_level} />
      </div>

      {/* ── Two-column layout ─────────────────────────────────────── */}
      <div className="grid-2 fade-up fade-up-d2">

        {/* Left: extracted fields + face */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

          <Section title="Extracted Document Fields">
            <div className="card">
              {[
                ['Name',            fields.name],
                ['Date of Birth',   fields.dob],
                ['Gender',          fields.gender],
                ['Aadhaar Number',  fields.aadhaar_number],
                ['PAN Number',      fields.pan_number],
                ['Document No.',    fields.document_number],
                ['Pincode',         fields.pincode],
              ].map(([label, value]) => (
                <FieldRow key={label} label={label} value={value} />
              ))}
            </div>
          </Section>

          {data.face_verification && (
            <Section title="Face Verification">
              <FaceCard fv={data.face_verification} />
            </Section>
          )}

          {data.ml_classification && (
            <Section title="ML Document Classifier">
              <MLCard ml={data.ml_classification} />
            </Section>
          )}
        </div>

        {/* Right: confidence checklist */}
        <div>
          <Section title="Confidence Breakdown">
            <ConfidenceChecklist
              checks={data.checks || []}
              overallScore={data.overall_risk_score}
              riskLevel={data.risk_level}
              recommendation={data.recommendation}
              failedChecks={data.failed_checks || []}
            />
          </Section>
        </div>
      </div>

      {/* ── Tamper regions (if any) ───────────────────────────────── */}
      {data.tampering_regions?.length > 0 && (
        <Section title={`Tampering Regions (${data.tampering_regions.length} detected)`} delay={0.4}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {data.tampering_regions.slice(0, 5).map((r, i) => (
              <div key={i} className="card" style={{ padding: '0.75rem 1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
                <span className="text-secondary text-sm">Region {i + 1}</span>
                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                  {[
                    ['x', r.x], ['y', r.y], ['w', r.width], ['h', r.height],
                    ['brightness', r.brightness?.toFixed(1)],
                  ].map(([k, v]) => (
                    <span key={k} className="mono text-xs" style={{ color: 'var(--text-muted)' }}>
                      <span style={{ color: 'var(--accent-amber)' }}>{k}</span>={v}
                    </span>
                  ))}
                </div>
                <div className="progress-track" style={{ width: 80, flexShrink: 0 }}>
                  <div className="progress-fill amber" style={{ width: `${Math.min(100, (r.brightness ?? 0) / 255 * 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* ── Try Again ─────────────────────────────────────────────── */}
      <div style={{ textAlign: 'center', paddingTop: '0.5rem' }}>
        <button
          id="reset-btn"
          onClick={onReset}
          className="btn btn-secondary"
        >
          ← Verify Another Document
        </button>
      </div>
    </div>
  );
}
