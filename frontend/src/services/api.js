/* API service — thin wrapper around the DocVerify backend */

const BASE = '/api';

/**
 * POST /api/verify — single document
 * @param {File} file
 */
export async function verifyDocument(file) {
  const form = new FormData();
  form.append('file', file);

  const res = await fetch(`${BASE}/verify`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/**
 * POST /api/verify-with-face — document + selfie
 * @param {File} documentFile
 * @param {File} selfieFile
 */
export async function verifyWithFace(documentFile, selfieFile) {
  const form = new FormData();
  form.append('document_file', documentFile);
  form.append('selfie_file',   selfieFile);

  const res = await fetch(`${BASE}/verify-with-face`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/**
 * GET /api/health
 */
export async function checkHealth() {
  const res = await fetch(`${BASE}/health`);
  return res.json();
}
