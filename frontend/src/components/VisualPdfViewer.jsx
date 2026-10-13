import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  ChevronLeft, 
  ChevronRight, 
  Search, 
  ExternalLink, 
  Maximize2, 
  BookOpen, 
  FileCheck 
} from 'lucide-react';
import { fetchDocumentPage, getDocumentPdfUrl } from '../services/api';

export default function VisualPdfViewer({ documents, initialDoc, initialPage }) {
  const [selectedDoc, setSelectedDoc] = useState(initialDoc || (documents[0]?.document_name || ''));
  const [currentPage, setCurrentPage] = useState(initialPage || 1);
  const [pageData, setPageData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [searchHighlight, setSearchHighlight] = useState('');

  // Sync when initialDoc / initialPage props change
  useEffect(() => {
    if (initialDoc) setSelectedDoc(initialDoc);
    if (initialPage) setCurrentPage(initialPage);
  }, [initialDoc, initialPage]);

  // Fetch page text whenever doc or page changes
  useEffect(() => {
    if (!selectedDoc) return;
    loadPageText(selectedDoc, currentPage);
  }, [selectedDoc, currentPage]);

  const loadPageText = async (docName, pageNum) => {
    setIsLoading(true);
    try {
      const data = await fetchDocumentPage(docName, pageNum);
      const text = data.text_content || data.text || '';
      setPageData({
        ...data,
        text,
        text_content: text
      });
    } catch (err) {
      setPageData({
        document: docName,
        page: pageNum,
        text: `Error loading page text: ${err.message}`,
        text_content: '',
        total_pages: 1
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handlePrevPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNextPage = () => {
    const maxPages = pageData?.total_pages || 1;
    if (currentPage < maxPages) setCurrentPage(currentPage + 1);
  };

  // Helper to highlight search keywords in extracted text
  const renderHighlightedText = (text, query) => {
    if (!query || !query.trim() || !text) return text;
    try {
      const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const parts = text.split(new RegExp(`(${escaped})`, 'gi'));
      return parts.map((part, i) => 
        part.toLowerCase() === query.toLowerCase() ? (
          <mark key={i}>{part}</mark>
        ) : (
          part
        )
      );
    } catch (e) {
      return text;
    }
  };

  const pdfUrl = selectedDoc ? getDocumentPdfUrl(selectedDoc, currentPage) : '';
  const isPdf = selectedDoc?.toLowerCase().endsWith('.pdf');

  return (
    <div style={{ height: 'calc(100vh - 68px)', display: 'flex', flexDirection: 'column', background: 'var(--bg-app)' }}>
      
      {/* Top Controls Bar */}
      <div style={{
        height: '60px',
        borderBottom: '1px solid var(--border-subtle)',
        background: 'var(--bg-sidebar)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        gap: '16px'
      }}>
        {/* Document Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <BookOpen size={18} color="#818cf8" />
          <select
            value={selectedDoc}
            onChange={(e) => {
              setSelectedDoc(e.target.value);
              setCurrentPage(1);
            }}
            style={{ width: '280px', padding: '6px 12px', fontSize: '0.85rem' }}
          >
            {documents.map((d) => (
              <option key={d.document_name} value={d.document_name}>
                {d.document_name} ({d.page_count} pgs)
              </option>
            ))}
          </select>
        </div>

        {/* Page Navigation */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button 
            onClick={handlePrevPage} 
            disabled={currentPage <= 1}
            className="btn btn-secondary btn-sm"
          >
            <ChevronLeft size={14} />
          </button>
          
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Page <strong style={{ color: 'var(--text-primary)' }}>{currentPage}</strong> of{' '}
            {pageData?.total_pages || 1}
          </span>

          <button 
            onClick={handleNextPage} 
            disabled={currentPage >= (pageData?.total_pages || 1)}
            className="btn btn-secondary btn-sm"
          >
            <ChevronRight size={14} />
          </button>
        </div>

        {/* Text Keyword Highlighter Search */}
        <div style={{ position: 'relative', width: '260px' }}>
          <Search size={14} color="var(--text-dim)" style={{ position: 'absolute', left: '10px', top: '10px' }} />
          <input
            type="text"
            value={searchHighlight}
            onChange={(e) => setSearchHighlight(e.target.value)}
            placeholder="Highlight keyword in text..."
            style={{ padding: '6px 10px 6px 32px', fontSize: '0.8rem' }}
          />
        </div>

        {/* External Link */}
        {pdfUrl && (
          <a 
            href={pdfUrl} 
            target="_blank" 
            rel="noopener noreferrer" 
            className="btn btn-secondary btn-sm"
            title="Open in new browser tab"
          >
            <ExternalLink size={13} />
            <span>Open Native</span>
          </a>
        )}
      </div>

      {/* Dual Viewport Studio */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        
        {/* Left: Extracted Page Text Reader with Search Highlights */}
        <div style={{
          flex: 1,
          borderRight: '1px solid var(--border-subtle)',
          padding: '24px 32px',
          overflowY: 'auto',
          background: 'rgba(11, 15, 25, 0.4)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileCheck size={18} color="#22d3ee" />
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700 }}>
                Verified Extracted Page Text
              </h3>
            </div>
            {(pageData?.text_content || pageData?.text) && (
              <span className="badge badge-indigo">
                {(pageData.text_content || pageData.text).length} characters
              </span>
            )}
          </div>

          {isLoading ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
              Loading extracted text for Page {currentPage}...
            </div>
          ) : (pageData?.text_content || pageData?.text) ? (
            <div 
              className="glass-panel" 
              style={{
                padding: '24px',
                fontSize: '0.9rem',
                lineHeight: 1.7,
                whiteSpace: 'pre-wrap',
                color: 'var(--text-primary)',
                background: 'rgba(15, 23, 42, 0.5)'
              }}
            >
              {renderHighlightedText(pageData.text_content || pageData.text, searchHighlight)}
            </div>
          ) : (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
              No text content extracted for this page. (May be an image-only / scanned page).
            </div>
          )}
        </div>

        {/* Right: Embedded Native PDF Viewer */}
        <div style={{ flex: 1.2, height: '100%', position: 'relative', background: '#1e293b' }}>
          {isPdf ? (
            <iframe
              src={pdfUrl}
              title={`PDF View: ${selectedDoc}`}
              style={{
                width: '100%',
                height: '100%',
                border: 'none',
                background: '#0f172a'
              }}
            />
          ) : (
            <div style={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '40px',
              textAlign: 'center',
              color: 'var(--text-muted)'
            }}>
              <FileText size={48} color="var(--accent-primary)" style={{ marginBottom: '16px' }} />
              <h3>Native PDF view available for .pdf documents</h3>
              <p style={{ marginTop: '8px', fontSize: '0.85rem' }}>
                '{selectedDoc}' is a {selectedDoc?.split('.').pop()?.toUpperCase()} document.
                Refer to the verified extracted text reader on the left.
              </p>
            </div>
          )}
        </div>

      </div>

    </div>
  );
}
