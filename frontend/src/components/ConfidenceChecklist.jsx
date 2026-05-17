import React from 'react';

const STATUS_META = {
  PASS: { label: 'Pass',    color: 'green', icon: '✓' },
  WARN: { label: 'Warning', color: 'amber', icon: '⚠' },
  FAIL: { label: 'Fail',    color: 'red',   icon: '✕' },
};

function CheckRow({ check, index }) {
  const meta  = STATUS_META[check.status] || STATUS_META.WARN;
  const score = check.score ?? 0;

  return (
    <div
      className="card fade-up"
      style={{ animationDelay: `${index * 0.05}s`, padding: '1.1rem 1.25rem' }}
    >
      <div className="flex items-center justify-between gap-4">
        {/* Left: icon + text */}
        <div className="flex items-center gap-3" style={{ minWidth: 0 }}>
          <div
            style={{
              width: 34, height: 34, borderRadius: '50%', flexShrink: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '1rem', fontWeight: 700,
              background: meta.color === 'green' ? 'rgba(16,185,129,0.15)'
                        : meta.color === 'amber' ? 'rgba(245,158,11,0.15)'
                        : 'rgba(239,68,68,0.15)',
              color: meta.color === 'green' ? 'var(--accent-green)'
                   : meta.color === 'amber' ? 'var(--accent-amber)'
                   : 'var(--accent-red)',
            }}
          >
            {meta.icon}
          </div>
          <div style={{ minWidth: 0 }}>
            <p className="font-semibold" style={{ fontSize: '0.92rem' }}>{check.name}</p>
            <p className="text-secondary text-xs mt-1" style={{ lineHeight: 1.4 }}>
              {check.description}
            </p>
          </div>
        </div>

        {/* Right: score + badge */}
        <div className="flex items-center gap-3" style={{ flexShrink: 0 }}>
          <span
            className="mono font-bold"
            style={{
              fontSize: '1.15rem',
              color: meta.color === 'green' ? 'var(--accent-green)'
                   : meta.color === 'amber' ? 'var(--accent-amber)'
                   : 'var(--accent-red)',
            }}
          >
            {score.toFixed(0)}%
          </span>
          <span className={`badge badge-${meta.color === 'green' ? 'pass' : meta.color === 'amber' ? 'warn' : 'fail'}`}>
            {meta.label}
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="progress-track mt-2">
        <div
          className={`progress-fill ${meta.color}`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}

export default function ConfidenceChecklist({ checks = [], overallScore, riskLevel, recommendation, failedChecks = [] }) {
  const riskColor = riskLevel === 'LOW' ? 'var(--accent-green)'
                  : riskLevel === 'MEDIUM' ? 'var(--accent-amber)'
                  : 'var(--accent-red)';

  const riskGlow = riskLevel === 'LOW' ? 'rgba(16,185,129,0.2)'
                 : riskLevel === 'MEDIUM' ? 'rgba(245,158,11,0.2)'
                 : 'rgba(239,68,68,0.2)';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

      {/* ── Overall Score ──────────────────────────────────────────── */}
      <div
        className="card fade-up"
        style={{
          border: `1px solid ${riskColor}33`,
          boxShadow: `0 0 32px ${riskGlow}`,
        }}
      >
        <div className="flex items-center justify-between">
          <div>
            <p className="text-secondary text-sm font-semibold" style={{ textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Overall Risk Score
            </p>
            <h2
              className="mono"
              style={{ fontSize: '3.5rem', fontWeight: 900, color: riskColor, lineHeight: 1.1, marginTop: '0.25rem' }}
            >
              {overallScore?.toFixed(1)}%
            </h2>
            <div className="flex items-center gap-2 mt-2">
              <span className={`badge badge-${riskLevel === 'LOW' ? 'pass' : riskLevel === 'MEDIUM' ? 'warn' : 'fail'}`}>
                {riskLevel} RISK
              </span>
              {failedChecks.length > 0 && (
                <span className="badge badge-fail">{failedChecks.length} failed</span>
              )}
            </div>
          </div>

          {/* Circular indicator */}
          <svg width="90" height="90" style={{ flexShrink: 0 }}>
            <circle cx="45" cy="45" r="38" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="7" />
            <circle
              cx="45" cy="45" r="38" fill="none"
              stroke={riskColor}
              strokeWidth="7"
              strokeLinecap="round"
              strokeDasharray={`${2 * Math.PI * 38}`}
              strokeDashoffset={`${2 * Math.PI * 38 * (1 - (overallScore ?? 0) / 100)}`}
              transform="rotate(-90 45 45)"
              style={{ transition: 'stroke-dashoffset 1s ease' }}
            />
            <text x="45" y="50" textAnchor="middle" fill={riskColor}
              style={{ fontSize: '14px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>
              {overallScore?.toFixed(0)}%
            </text>
          </svg>
        </div>

        {/* Recommendation */}
        <div
          style={{
            marginTop: '1rem', padding: '0.85rem 1rem',
            borderRadius: 'var(--radius-sm)',
            background: `${riskColor}15`,
            border: `1px solid ${riskColor}30`,
            fontSize: '0.9rem', color: riskColor, fontWeight: 500,
          }}
        >
          {recommendation}
        </div>
      </div>

      {/* ── Checklist heading ─────────────────────────────────────── */}
      <div className="flex items-center gap-2 mt-2">
        <div style={{ height: 1, flex: 1, background: 'var(--border)' }} />
        <span className="text-muted text-xs font-semibold" style={{ textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          Verification Checks
        </span>
        <div style={{ height: 1, flex: 1, background: 'var(--border)' }} />
      </div>

      {/* ── Individual checks ──────────────────────────────────────── */}
      {checks.map((check, i) => (
        <CheckRow key={check.name} check={check} index={i} />
      ))}
    </div>
  );
}
