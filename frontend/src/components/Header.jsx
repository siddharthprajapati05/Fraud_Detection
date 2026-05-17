import React from 'react';

export default function Header({ backendOk }) {
  return (
    <header
      style={{
        position: 'sticky', top: 0, zIndex: 50,
        background: 'rgba(7,7,15,0.85)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid var(--border)',
        padding: '0.9rem 0',
      }}
    >
      <div className="container flex items-center justify-between">
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: 38, height: 38,
            background: 'linear-gradient(135deg,var(--accent-1),var(--accent-2))',
            borderRadius: '10px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '1.2rem', boxShadow: '0 4px 16px rgba(139,92,246,0.4)',
          }}>
            🛡
          </div>
          <div>
            <h1 style={{ fontSize: '1.15rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
              DocVerify <span className="gradient-text">AI</span>
            </h1>
            <p style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '-2px', letterSpacing: '0.04em' }}>
              KYC DOCUMENT VERIFICATION
            </p>
          </div>
        </div>

        {/* Right side */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <div style={{
              width: 8, height: 8, borderRadius: '50%',
              background: backendOk ? 'var(--accent-green)' : 'var(--accent-red)',
              boxShadow: `0 0 8px ${backendOk ? 'var(--accent-green)' : 'var(--accent-red)'}`,
              animation: backendOk ? 'pulse-glow 2s infinite' : 'none',
            }} />
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              {backendOk ? 'Backend Online' : 'Backend Offline'}
            </span>
          </div>

          {/* Feature pills */}
          {['ELA Fraud', 'OCR', 'Face AI', 'ResNet-50'].map(f => (
            <span key={f} className="badge badge-info" style={{ fontSize: '0.7rem' }}>{f}</span>
          ))}
        </div>
      </div>
    </header>
  );
}
