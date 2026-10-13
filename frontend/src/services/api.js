const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export async function fetchHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return {
      status: 'offline',
      vector_db_loaded: false,
      ollama_available: false,
      document_count: 0,
      active_documents: []
    };
  }
}

export async function submitQuery(payload) {
  const res = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Query failed with HTTP ${res.status}`);
  }
  return await res.json();
}

export async function submitComparison(payload) {
  const res = await fetch(`${API_BASE}/query/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Comparison failed with HTTP ${res.status}`);
  }
  return await res.json();
}

export async function fetchDocuments() {
  const res = await fetch(`${API_BASE}/documents`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Upload failed with HTTP ${res.status}`);
  }
  return await res.json();
}

export async function deleteDocument(docName) {
  const res = await fetch(`${API_BASE}/documents/${encodeURIComponent(docName)}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

export async function fetchDocumentPage(docName, pageNum) {
  const res = await fetch(`${API_BASE}/documents/${encodeURIComponent(docName)}/page/${pageNum}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

export async function fetchPageSummary(docName, pageNum, forceRefresh = false) {
  const url = `${API_BASE}/documents/${encodeURIComponent(docName)}/page/${pageNum}/summary${forceRefresh ? '?force_refresh=true' : ''}`;
  const res = await fetch(url);
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Summary failed with HTTP ${res.status}`);
  }
  return await res.json();
}

export function getDocumentPdfUrl(docName, pageNum = 1) {
  return `${API_BASE}/documents/${encodeURIComponent(docName)}/file#page=${pageNum}`;
}

export function getDocumentPreviewPdfUrl(docName, pageNum = 1) {
  return `${API_BASE}/documents/${encodeURIComponent(docName)}/preview_pdf#page=${pageNum}`;
}

export function getDocumentImageUrl(docName, pageNum = 1) {
  return `${API_BASE}/documents/${encodeURIComponent(docName)}/page/${pageNum}/image`;
}

export function getDocumentDownloadUrl(docName) {
  return `${API_BASE}/documents/${encodeURIComponent(docName)}/file`;
}



export async function fetchAnalytics() {
  try {
    const res = await fetch(`${API_BASE}/documents/analytics`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return null;
  }
}
