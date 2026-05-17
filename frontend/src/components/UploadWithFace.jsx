import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { verifyDocument, verifyWithFace } from '../services/api.js';

function FileDropzone({ label, icon, accept, file, onFile, color = 'var(--accent-1)', id }) {
  const onDrop = useCallback(accepted => {
    if (accepted[0]) onFile(accepted[0]);
  }, [onFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
    maxFiles: 1,
  });

  const preview = file ? URL.createObjectURL(file) : null;

  return (
    <div>
      <label
        htmlFor={id}
        style={{
          display: 'block', marginBottom: '0.6rem',
          fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-secondary)',
          textTransform: 'uppercase', letterSpacing: '0.07em',
        }}
      >
        {label}
      </label>
      <div
        {...getRootProps()}
        id={id}
        className={`dropzone${isDragActive ? ' active' : ''}${file ? ' has-file' : ''}`}
        style={{ borderColor: file ? 'var(--accent-green)' : isDragActive ? color : undefined }}
      >
        <input {...getInputProps()} />
        {preview ? (
          <div>
            <img
              src={preview}
              alt="preview"
              style={{
                maxHeight: 120, maxWidth: '100%',
                objectFit: 'contain',
                borderRadius: 'var(--radius-sm)',
                marginBottom: '0.75rem',
              }}
            />
            <p className="text-xs text-secondary">{file.name} — click to replace</p>
          </div>
        ) : (
          <div style={{ pointerEvents: 'none' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>{icon}</div>
            <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
              {isDragActive ? 'Drop it here…' : 'Drag & drop or click to browse'}
            </p>
            <p className="text-secondary text-sm">JPG, PNG, WEBP — max 10 MB</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function UploadWithFace({ onResult }) {
  const [docFile,     setDocFile]     = useState(null);
  const [selfieFile,  setSelfieFile]  = useState(null);
  const [mode,        setMode]        = useState('doc');   // 'doc' | 'face'
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState(null);

  const handleVerify = async () => {
    if (!docFile) { setError('Please upload a document image.'); return; }
    if (mode === 'face' && !selfieFile) { setError('Please upload a selfie.'); return; }
    setError(null);
    setLoading(true);
    try {
      const data = mode === 'face'
        ? await verifyWithFace(docFile, selfieFile)
        : await verifyDocument(docFile);
      onResult(data);
    } catch (err) {
      setError(err.message || 'Verification failed. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  const modeTab = (m, label, icon) => (
    <button
      onClick={() => setMode(m)}
      style={{
        flex: 1, padding: '0.65rem 1rem',
        background: mode === m ? 'linear-gradient(135deg,var(--accent-1),var(--accent-2))' : 'transparent',
        color: mode === m ? '#fff' : 'var(--text-secondary)',
        border: 'none', borderRadius: 'var(--radius-sm)',
        fontFamily: 'inherit', fontWeight: 600, fontSize: '0.9rem',
        cursor: 'pointer', transition: 'var(--transition)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem',
      }}
    >
      <span>{icon}</span>{label}
    </button>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

      {/* ── Mode Toggle ───────────────────────────────────────────── */}
      <div
        style={{
          display: 'flex', gap: '4px',
          background: 'var(--bg-card)', borderRadius: 'var(--radius-md)',
          padding: '4px', border: '1px solid var(--border)',
        }}
      >
        {modeTab('doc',  'Document Only', '📄')}
        {modeTab('face', 'With Face Check', '🧬')}
      </div>

      {/* ── Dropzones ─────────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: mode === 'face' ? '1fr 1fr' : '1fr', gap: '1.5rem' }}>
        <FileDropzone
          id="doc-upload"
          label="Step 1 — Upload ID Document"
          icon="🪪"
          file={docFile}
          onFile={setDocFile}
          color="var(--accent-2)"
        />

        {mode === 'face' && (
          <FileDropzone
            id="selfie-upload"
            label="Step 2 — Upload Live Selfie"
            icon="🤳"
            file={selfieFile}
            onFile={setSelfieFile}
            color="var(--accent-green)"
          />
        )}
      </div>

      {/* ── Error ─────────────────────────────────────────────────── */}
      {error && (
        <div style={{
          padding: '0.85rem 1rem', borderRadius: 'var(--radius-sm)',
          background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
          color: 'var(--accent-red)', fontSize: '0.9rem',
        }}>
          ⚠ {error}
        </div>
      )}

      {/* ── Submit ─────────────────────────────────────────────────── */}
      <button
        id="verify-btn"
        onClick={handleVerify}
        disabled={loading || !docFile}
        className="btn btn-primary btn-lg w-full"
        style={{ marginTop: '0.25rem' }}
      >
        {loading ? (
          <><div className="spinner" />  Analysing…</>
        ) : (
          <><span>🔍</span> Run KYC Verification</>
        )}
      </button>

      {/* Tips */}
      {!loading && (
        <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
          {[
            '✦  Use a clear, flat image — avoid glare and shadows',
            '✦  Ensure all 4 corners of the ID are visible',
            mode === 'face' && '✦  Selfie: neutral background, good lighting, face centred',
          ].filter(Boolean).map((tip, i) => (
            <li key={i} className="text-muted text-xs">{tip}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
