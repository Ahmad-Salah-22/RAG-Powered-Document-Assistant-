import React, { useState, useRef } from 'react';
import { 
  UploadCloud, 
  FileText, 
  Trash2, 
  Search, 
  Eye, 
  AlertTriangle, 
  CheckCircle2, 
  Layers, 
  FileSpreadsheet, 
  Presentation, 
  FileCheck 
} from 'lucide-react';
import { uploadDocument, deleteDocument } from '../services/api';

export default function DocumentLibrary({ documents, onRefresh, onViewDocument }) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadFeedback, setUploadFeedback] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteConfirmDoc, setDeleteConfirmDoc] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileUpload = async (file) => {
    if (!file) return;
    setIsUploading(true);
    setUploadFeedback(null);

    try {
      const res = await uploadDocument(file);
      setUploadFeedback({
        type: 'success',
        message: `Successfully indexed '${res.document_name}' (${res.chunks_indexed} chunks, ${res.pages} pages).`
      });
      onRefresh();
    } catch (err) {
      setUploadFeedback({
        type: 'error',
        message: `Upload error: ${err.message}`
      });
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (docName) => {
    try {
      await deleteDocument(docName);
      setDeleteConfirmDoc(null);
      setUploadFeedback({
        type: 'success',
        message: `Removed '${docName}' from vector store.`
      });
      onRefresh();
    } catch (err) {
      setUploadFeedback({
        type: 'error',
        message: `Delete failed: ${err.message}`
      });
    }
  };

  const getFormatBadge = (docName) => {
    const ext = docName.split('.').pop().toLowerCase();
    switch (ext) {
      case 'pdf':
        return <span className="badge badge-rose">PDF</span>;
      case 'docx':
        return <span className="badge badge-indigo">Word</span>;
      case 'pptx':
        return <span className="badge badge-amber">PowerPoint</span>;
      case 'csv':
      case 'xlsx':
        return <span className="badge badge-emerald">Sheet</span>;
      default:
        return <span className="badge badge-cyan">{ext.toUpperCase()}</span>;
    }
  };

  const filteredDocs = documents.filter(d => 
    d.document_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div style={{ padding: '32px 48px', height: 'calc(100vh - 68px)', overflowY: 'auto' }}>
      
      {/* Title & Stats */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Document Corpus Library</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Unified multimodal knowledge base indexed into persistent ChromaDB collections.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <div className="glass-panel" style={{ padding: '10px 18px', textAlign: 'center' }}>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--accent-primary)' }}>{documents.length}</div>
            <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>Indexed Documents</div>
          </div>
          <div className="glass-panel" style={{ padding: '10px 18px', textAlign: 'center' }}>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
              {documents.reduce((acc, d) => acc + (d.chunk_count || 0), 0)}
            </div>
            <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>Total Vector Chunks</div>
          </div>
        </div>
      </div>

      {/* Drag & Drop Upload Zone */}
      <div 
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          if (e.dataTransfer.files?.[0]) handleFileUpload(e.dataTransfer.files[0]);
        }}
        className="glass-panel"
        style={{
          border: '2px dashed var(--border-medium)',
          borderRadius: '16px',
          padding: '36px',
          textAlign: 'center',
          cursor: isUploading ? 'not-allowed' : 'pointer',
          background: 'rgba(255, 255, 255, 0.015)',
          marginBottom: '28px',
          transition: 'all 0.2s ease'
        }}
      >
        <input 
          ref={fileInputRef}
          type="file" 
          accept=".pdf,.docx,.pptx,.csv,.xlsx,.txt,.md,.markdown" 
          onChange={(e) => handleFileUpload(e.target.files?.[0])}
          style={{ display: 'none' }}
        />
        <div style={{
          width: '56px',
          height: '56px',
          borderRadius: '16px',
          background: 'rgba(99, 102, 241, 0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 14px'
        }}>
          <UploadCloud size={28} color="#818cf8" className={isUploading ? 'pulse-indicator' : ''} />
        </div>
        <div style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '6px' }}>
          {isUploading ? 'Extracting, Chunking & Embedding Document...' : 'Click or Drag & Drop to Upload Document'}
        </div>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Supports PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx), CSV, Markdown (.md), and TXT files.
        </p>
      </div>

      {/* Upload Feedback Toast */}
      {uploadFeedback && (
        <div 
          className="animate-fade-in"
          style={{
            padding: '12px 18px',
            borderRadius: '10px',
            marginBottom: '24px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            fontSize: '0.875rem',
            background: uploadFeedback.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
            border: `1px solid ${uploadFeedback.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
            color: uploadFeedback.type === 'success' ? '#34d399' : '#fb7185'
          }}
        >
          {uploadFeedback.type === 'success' ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
          <span>{uploadFeedback.message}</span>
        </div>
      )}

      {/* Filter & Search Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div style={{ position: 'relative', width: '320px' }}>
          <Search size={15} color="var(--text-dim)" style={{ position: 'absolute', left: '12px', top: '13px' }} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search documents by name..."
            style={{ paddingLeft: '36px' }}
          />
        </div>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Showing {filteredDocs.length} of {documents.length} files
        </span>
      </div>

      {/* Document Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '18px' }}>
        {filteredDocs.map((doc) => (
          <div 
            key={doc.document_name}
            className="glass-panel"
            style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}
          >
            {/* Top Card Row */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <FileText size={20} color="#818cf8" />
                <div>
                  <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', wordBreak: 'break-all' }}>
                    {doc.document_name}
                  </h3>
                  <div style={{ display: 'flex', gap: '6px', marginTop: '4px' }}>
                    {getFormatBadge(doc.document_name)}
                    <span className="badge badge-indigo">{doc.chunk_count} Chunks</span>
                    <span className="badge badge-cyan">{doc.page_count} Pages</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Document Abstract Snippet */}
            {doc.summary_preview && (
              <p style={{ fontSize: '0.775rem', color: 'var(--text-muted)', lineHeight: 1.5, background: 'rgba(0,0,0,0.25)', padding: '8px 12px', borderRadius: '8px' }}>
                "{doc.summary_preview}"
              </p>
            )}

            {/* Meta tags */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.725rem', color: 'var(--text-dim)', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
              <span>Chars: {doc.char_count?.toLocaleString() || 'N/A'}</span>
              <span>{doc.file_size_bytes ? `${(doc.file_size_bytes / 1024).toFixed(1)} KB` : 'Local file'}</span>
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', gap: '8px', marginTop: 'auto' }}>
              <button
                onClick={() => onViewDocument(doc.document_name, 1)}
                className="btn btn-secondary btn-sm"
                style={{ flex: 1 }}
              >
                <Eye size={13} />
                <span>View &amp; Verify</span>
              </button>

              {deleteConfirmDoc === doc.document_name ? (
                <div style={{ display: 'flex', gap: '4px' }}>
                  <button
                    onClick={() => handleDelete(doc.document_name)}
                    className="btn btn-danger btn-sm"
                  >
                    Confirm
                  </button>
                  <button
                    onClick={() => setDeleteConfirmDoc(null)}
                    className="btn btn-secondary btn-sm"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setDeleteConfirmDoc(doc.document_name)}
                  className="btn btn-icon btn-sm"
                  title="Delete Document"
                  style={{ border: '1px solid var(--border-subtle)' }}
                >
                  <Trash2 size={14} color="var(--accent-rose)" />
                </button>
              )}
            </div>

          </div>
        ))}

        {filteredDocs.length === 0 && (
          <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            No documents matched your search filter.
          </div>
        )}
      </div>

    </div>
  );
}
