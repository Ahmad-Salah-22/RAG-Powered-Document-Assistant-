import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  ChevronLeft, 
  ChevronRight, 
  Search, 
  ExternalLink, 
  BookOpen, 
  FileCheck,
  Sparkles,
  Copy,
  Check,
  RotateCw,
  ListChecks,
  AlertCircle,
  Lightbulb,
  Presentation,
  Download,
  Layers,
  Eye,
  Maximize2
} from 'lucide-react';
import { 
  fetchDocumentPage, 
  fetchPageSummary, 
  getDocumentPdfUrl,
  getDocumentPreviewPdfUrl,
  getDocumentImageUrl,
  getDocumentDownloadUrl
} from '../services/api';

export default function VisualPdfViewer({ documents, initialDoc, initialPage, onNavigateToLibrary }) {
  const [selectedDoc, setSelectedDoc] = useState(initialDoc || (documents[0]?.document_name || ''));
  const [currentPage, setCurrentPage] = useState(initialPage || 1);
  const [pageData, setPageData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeLeftTab, setActiveLeftTab] = useState('summary'); // 'summary' | 'extracted_text'
  const [rightViewMode, setRightViewMode] = useState('pdf'); // 'pdf' (Real Embedded File) | 'image' (Real High-Res Slide Image)

  // Page Summary State
  const [pageSummaries, setPageSummaries] = useState({});
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [summaryError, setSummaryError] = useState(null);
  const [copiedSummary, setCopiedSummary] = useState(false);
  const [copiedText, setCopiedText] = useState(false);
  const [searchHighlight, setSearchHighlight] = useState('');

  // Sync when initialDoc / initialPage props change
  useEffect(() => {
    if (initialDoc) setSelectedDoc(initialDoc);
    if (initialPage) setCurrentPage(initialPage);
  }, [initialDoc, initialPage]);

  // When documents change, pick first if none selected
  useEffect(() => {
    if ((!selectedDoc || !documents.some(d => d.document_name === selectedDoc)) && documents?.length > 0) {
      setSelectedDoc(documents[0].document_name);
      setCurrentPage(1);
    }
  }, [documents]);

  // Fetch page text and summary whenever doc or page changes
  useEffect(() => {
    if (!selectedDoc) return;
    loadPageText(selectedDoc, currentPage);
    loadSummary(selectedDoc, currentPage, false);
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

  const loadSummary = async (docName, pageNum, forceRefresh = false) => {
    const cacheKey = `${docName}_p${pageNum}`;
    if (!forceRefresh && pageSummaries[cacheKey]) {
      return;
    }

    setIsSummarizing(true);
    setSummaryError(null);
    try {
      const summaryData = await fetchPageSummary(docName, pageNum, forceRefresh);
      setPageSummaries(prev => ({
        ...prev,
        [cacheKey]: summaryData
      }));
    } catch (err) {
      console.warn(`Could not summarize page ${pageNum} of ${docName}:`, err);
      setSummaryError(err.message);
    } finally {
      setIsSummarizing(false);
    }
  };

  const currentCacheKey = `${selectedDoc}_p${currentPage}`;
  const currentSummary = pageSummaries[currentCacheKey];

  const handlePrevPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNextPage = () => {
    const maxPages = pageData?.total_pages || 1;
    if (currentPage < maxPages) setCurrentPage(currentPage + 1);
  };

  const handleCopySummary = () => {
    if (!currentSummary) return;
    const textToCopy = `### Page ${currentPage} Summary: ${currentSummary.main_topic || selectedDoc}\n\n${currentSummary.summary}\n\n**Key Points:**\n${(currentSummary.key_points || []).map(p => `- ${p}`).join('\n')}`;
    navigator.clipboard.writeText(textToCopy);
    setCopiedSummary(true);
    setTimeout(() => setCopiedSummary(false), 2000);
  };

  const handleCopyExtractedText = () => {
    const text = pageData?.text_content || pageData?.text || '';
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedText(true);
    setTimeout(() => setCopiedText(false), 2000);
  };

  // Helper to highlight search keywords in extracted text
  const renderHighlightedText = (text, query) => {
    if (!query || !query.trim() || !text) return text;
    try {
      const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const parts = text.split(new RegExp(`(${escaped})`, 'gi'));
      return parts.map((part, i) => 
        part.toLowerCase() === query.toLowerCase() ? (
          <mark key={i} style={{ background: '#fef08a', color: '#854d0e', padding: '1px 3px', borderRadius: '3px' }}>{part}</mark>
        ) : (
          part
        )
      );
    } catch (e) {
      return text;
    }
  };

  const ext = selectedDoc ? selectedDoc.split('.').pop()?.toLowerCase() : '';
  const isPdf = ext === 'pdf';
  const isPresentation = ext === 'pptx' || ext === 'ppt';
  
  const pdfUrl = selectedDoc ? (isPdf ? getDocumentPdfUrl(selectedDoc, currentPage) : getDocumentPreviewPdfUrl(selectedDoc, currentPage)) : '';
  const imageUrl = selectedDoc ? getDocumentImageUrl(selectedDoc, currentPage) : '';
  const downloadUrl = selectedDoc ? getDocumentDownloadUrl(selectedDoc) : '';


  // Keyboard arrow navigation for slides/pages
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target?.tagName)) return;
      if (e.key === 'ArrowLeft') {
        handlePrevPage();
      } else if (e.key === 'ArrowRight') {
        handleNextPage();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentPage, pageData]);

  if (!documents || documents.length === 0) {
    return (
      <div style={{ height: 'calc(100vh - 68px)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-app)', padding: '40px', textAlign: 'center' }}>
        <div style={{
          width: '68px',
          height: '68px',
          borderRadius: '20px',
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(6, 182, 212, 0.2))',
          border: '1px solid rgba(99, 102, 241, 0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '20px'
        }}>
          <BookOpen size={34} color="#818cf8" />
        </div>
        <h2 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '8px' }}>
          No Documents in Library
        </h2>
        <p style={{ color: 'var(--text-secondary)', maxWidth: '480px', marginBottom: '24px', fontSize: '0.925rem', lineHeight: 1.6 }}>
          Upload any PDF or research document in the Document Library to inspect pages, read verified extracted text, and generate AI page summaries.
        </p>
        {onNavigateToLibrary && (
          <button onClick={onNavigateToLibrary} className="btn btn-primary" style={{ padding: '10px 20px' }}>
            Go to Document Library
          </button>
        )}
      </div>
    );
  }

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
            title="Previous Page"
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
            title="Next Page"
          >
            <ChevronRight size={14} />
          </button>
        </div>

        {/* Text Keyword Highlighter Search */}
        <div style={{ position: 'relative', width: '240px' }}>
          <Search size={14} color="var(--text-dim)" style={{ position: 'absolute', left: '10px', top: '10px' }} />
          <input
            type="text"
            value={searchHighlight}
            onChange={(e) => setSearchHighlight(e.target.value)}
            placeholder="Search keywords..."
            style={{ padding: '6px 10px 6px 32px', fontSize: '0.8rem' }}
          />
        </div>

        {/* Top Header Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {pdfUrl && (
            <a 
              href={pdfUrl} 
              target="_blank" 
              rel="noopener noreferrer" 
              className="btn btn-secondary btn-sm"
              title="Open native or synthesized PDF preview in new tab"
            >
              <ExternalLink size={13} />
              <span>{isPdf ? 'Open Native PDF' : 'Open PDF Preview'}</span>
            </a>
          )}
          {downloadUrl && !isPdf && (
            <a 
              href={downloadUrl} 
              download={selectedDoc}
              className="btn btn-secondary btn-sm"
              title={`Download original ${selectedDoc}`}
            >
              <Download size={13} />
              <span>Download {ext.toUpperCase()}</span>
            </a>
          )}
        </div>

      </div>

      {/* Dual Viewport Studio */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        
        {/* Left Column: AI Page Summary & Verified Extracted Text Tabs */}
        <div style={{
          flex: 1.1,
          borderRight: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          background: 'var(--bg-app)',
          overflow: 'hidden'
        }}>
          {/* Left Column Subheader Tabs */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid var(--border-subtle)',
            padding: '8px 20px',
            background: 'var(--bg-glass-elevated)'
          }}>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => setActiveLeftTab('summary')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 14px',
                  borderRadius: '8px',
                  border: activeLeftTab === 'summary' ? '1px solid var(--badge-indigo-border)' : '1px solid transparent',
                  background: activeLeftTab === 'summary' ? 'var(--badge-indigo-bg)' : 'transparent',
                  color: activeLeftTab === 'summary' ? 'var(--badge-indigo-text)' : 'var(--text-secondary)',
                  fontSize: '0.825rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <Sparkles size={14} color={activeLeftTab === 'summary' ? 'var(--badge-indigo-text)' : 'currentColor'} />
                <span>AI Page Summary</span>
                {currentSummary && (
                  <span className="badge badge-indigo" style={{ fontSize: '0.65rem', padding: '1px 5px' }}>
                    Ready
                  </span>
                )}
              </button>

              <button
                onClick={() => setActiveLeftTab('extracted_text')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 14px',
                  borderRadius: '8px',
                  border: activeLeftTab === 'extracted_text' ? '1px solid var(--badge-cyan-border)' : '1px solid transparent',
                  background: activeLeftTab === 'extracted_text' ? 'var(--badge-cyan-bg)' : 'transparent',
                  color: activeLeftTab === 'extracted_text' ? 'var(--badge-cyan-text)' : 'var(--text-secondary)',
                  fontSize: '0.825rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <FileCheck size={14} color={activeLeftTab === 'extracted_text' ? 'var(--badge-cyan-text)' : 'currentColor'} />
                <span>Extracted Text</span>
                {(pageData?.text_content || pageData?.text) && (
                  <span style={{ fontSize: '0.675rem', color: 'var(--text-dim)' }}>
                    ({(pageData.text_content || pageData.text).length} chars)
                  </span>
                )}
              </button>
            </div>

            {/* Action buttons on tab header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {activeLeftTab === 'summary' && (
                <>
                  <button
                    onClick={() => loadSummary(selectedDoc, currentPage, true)}
                    disabled={isSummarizing}
                    className="btn btn-secondary btn-sm"
                    style={{ padding: '4px 8px', fontSize: '0.725rem' }}
                    title="Regenerate Page Summary"
                  >
                    <RotateCw size={12} className={isSummarizing ? 'pulse-indicator' : ''} />
                    <span>Regenerate</span>
                  </button>

                  <button
                    onClick={handleCopySummary}
                    disabled={!currentSummary}
                    className="btn btn-secondary btn-sm"
                    style={{ padding: '4px 8px', fontSize: '0.725rem' }}
                    title="Copy Page Summary"
                  >
                    {copiedSummary ? <Check size={12} color="#10b981" /> : <Copy size={12} />}
                    <span>{copiedSummary ? 'Copied!' : 'Copy'}</span>
                  </button>
                </>
              )}

              {activeLeftTab === 'extracted_text' && (
                <button
                  onClick={handleCopyExtractedText}
                  disabled={!pageData?.text_content && !pageData?.text}
                  className="btn btn-secondary btn-sm"
                  style={{ padding: '4px 8px', fontSize: '0.725rem' }}
                  title="Copy Full Page Text"
                >
                  {copiedText ? <Check size={12} color="#10b981" /> : <Copy size={12} />}
                  <span>{copiedText ? 'Copied!' : 'Copy Text'}</span>
                </button>
              )}
            </div>
          </div>

          {/* Left Column Scrollable Content Area */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
            
            {/* TAB 1: AI PAGE SUMMARY */}
            {activeLeftTab === 'summary' && (
              <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                
                {/* Topic Header Card */}
                <div className="glass-panel" style={{ padding: '16px 20px', borderLeft: '4px solid var(--accent-primary)', background: 'var(--badge-indigo-bg)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ fontSize: '0.725rem', fontWeight: 700, color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Page {currentPage} Primary Topic
                    </span>
                    {currentSummary?.model_used && (
                      <span className="badge badge-indigo" style={{ fontSize: '0.675rem' }}>
                        {currentSummary.model_used} • {currentSummary.latency_ms || 0}ms
                      </span>
                    )}
                  </div>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                    {isSummarizing ? (
                      <span style={{ color: 'var(--text-muted)' }}>Analyzing page topics &amp; extracting key insights...</span>
                    ) : (
                      currentSummary?.main_topic || `Page ${currentPage} Overview`
                    )}
                  </h3>
                </div>

                {isSummarizing ? (
                  <div style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'var(--badge-indigo-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px' }}>
                      <RotateCw size={18} color="var(--accent-primary)" className="pulse-indicator" />
                    </div>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>Generating AI Summary for Page {currentPage}...</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Reading page text and synthesizing core takeaways...</div>
                  </div>
                ) : summaryError ? (
                  <div className="glass-panel" style={{ padding: '16px', color: 'var(--accent-rose)', border: '1px solid rgba(244, 63, 94, 0.3)', display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <AlertCircle size={18} />
                    <span>Summary error: {summaryError}. You can review the raw extracted text in the Extracted Text tab.</span>
                  </div>
                ) : currentSummary ? (
                  <>
                    {/* Executive Narrative Summary */}
                    <div className="glass-panel" style={{ padding: '20px', background: 'var(--bg-card)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', color: 'var(--text-secondary)', fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                        <Lightbulb size={14} color="var(--accent-amber)" />
                        <span>Executive Narrative Summary</span>
                      </div>
                      <p style={{ fontSize: '0.925rem', lineHeight: 1.7, color: 'var(--text-primary)', margin: 0 }}>
                        {currentSummary.summary}
                      </p>
                    </div>

                    {/* Key Takeaways & Bullet Points */}
                    {currentSummary.key_points && currentSummary.key_points.length > 0 && (
                      <div className="glass-panel" style={{ padding: '20px', background: 'var(--bg-card)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: 'var(--text-secondary)', fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                          <ListChecks size={14} color="var(--accent-emerald)" />
                          <span>Core Takeaways &amp; Findings ({currentSummary.key_points.length})</span>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          {currentSummary.key_points.map((pt, ptIdx) => (
                            <div 
                              key={ptIdx}
                              style={{
                                display: 'flex',
                                alignItems: 'flex-start',
                                gap: '10px',
                                background: 'var(--card-subtle-bg)',
                                padding: '10px 14px',
                                borderRadius: '10px',
                                border: '1px solid var(--border-subtle)'
                              }}
                            >
                              <div style={{ marginTop: '2px', width: '18px', height: '18px', borderRadius: '50%', background: 'var(--badge-emerald-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                                <span style={{ fontSize: '0.675rem', fontWeight: 700, color: 'var(--badge-emerald-text)' }}>{ptIdx + 1}</span>
                              </div>
                              <span style={{ fontSize: '0.875rem', lineHeight: 1.55, color: 'var(--text-primary)' }}>
                                {pt}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No summary available for Page {currentPage}. Click "Regenerate" above to synthesize page content.
                  </div>
                )}

              </div>
            )}

            {/* TAB 2: FULL EXTRACTED TEXT */}
            {activeLeftTab === 'extracted_text' && (
              <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Machine-Extracted Text Reader
                  </span>
                  {(pageData?.text_content || pageData?.text) && (
                    <span className="badge badge-cyan" style={{ fontSize: '0.7rem' }}>
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
                      padding: '20px 24px',
                      fontSize: '0.9rem',
                      lineHeight: 1.7,
                      whiteSpace: 'pre-wrap',
                      color: 'var(--text-primary)',
                      background: 'var(--bg-card)'
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
            )}

          </div>
        </div>

        {/* Right Column: Real Document Viewer / High-Res Image View */}
        <div style={{
          flex: 1.25,
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          background: 'var(--bg-app)',
          position: 'relative',
          overflow: 'hidden'
        }}>
          {/* Right Column Subheader Switcher */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid var(--border-subtle)',
            padding: '8px 20px',
            background: 'var(--bg-glass-elevated)'
          }}>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => setRightViewMode('pdf')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 14px',
                  borderRadius: '8px',
                  border: rightViewMode === 'pdf' ? '1px solid var(--badge-indigo-border)' : '1px solid transparent',
                  background: rightViewMode === 'pdf' ? 'var(--badge-indigo-bg)' : 'transparent',
                  color: rightViewMode === 'pdf' ? 'var(--badge-indigo-text)' : 'var(--text-secondary)',
                  fontSize: '0.825rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <FileText size={14} color={rightViewMode === 'pdf' ? 'var(--badge-indigo-text)' : 'currentColor'} />
                <span>Real Document View ({ext.toUpperCase()})</span>
              </button>

              <button
                onClick={() => setRightViewMode('image')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 14px',
                  borderRadius: '8px',
                  border: rightViewMode === 'image' ? '1px solid var(--badge-cyan-border)' : '1px solid transparent',
                  background: rightViewMode === 'image' ? 'var(--badge-cyan-bg)' : 'transparent',
                  color: rightViewMode === 'image' ? 'var(--badge-cyan-text)' : 'var(--text-secondary)',
                  fontSize: '0.825rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <Eye size={14} color={rightViewMode === 'image' ? 'var(--badge-cyan-text)' : 'currentColor'} />
                <span>Real Slide Image (HD)</span>
              </button>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {pdfUrl && (
                <a
                  href={pdfUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-secondary btn-sm"
                  style={{ padding: '4px 8px', fontSize: '0.725rem' }}
                  title="Open real file in new browser tab"
                >
                  <ExternalLink size={12} />
                  <span>Open Tab</span>
                </a>
              )}
              {downloadUrl && (
                <a
                  href={downloadUrl}
                  download={selectedDoc}
                  className="btn btn-secondary btn-sm"
                  style={{ padding: '4px 8px', fontSize: '0.725rem' }}
                  title={`Download original ${selectedDoc}`}
                >
                  <Download size={12} />
                  <span>Download {ext.toUpperCase()}</span>
                </a>
              )}
            </div>
          </div>

          {/* VIEW 1: EMBEDDED REAL DOCUMENT VIEW (NATIVE IFRAME) */}
          {rightViewMode === 'pdf' && (
            <div style={{ flex: 1, height: '100%', position: 'relative' }}>
              <iframe
                src={pdfUrl}
                title={`Document View: ${selectedDoc}`}
                style={{
                  width: '100%',
                  height: '100%',
                  border: 'none',
                  background: 'var(--bg-app)'
                }}
              />

            </div>
          )}

          {/* VIEW 2: REAL HIGH-RESOLUTION SLIDE / PAGE IMAGE */}
          {rightViewMode === 'image' && (
            <div style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '16px 20px',
              overflowY: 'auto',
              background: 'radial-gradient(ellipse at top, rgba(30, 41, 59, 0.5) 0%, rgba(9, 13, 22, 0.98) 100%)'
            }}>
              {/* Real Rendered Slide Image */}
              <div 
                className="animate-fade-in"
                style={{
                  width: '100%',
                  maxWidth: '920px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  borderRadius: '12px',
                  overflow: 'hidden',
                  boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.8), 0 0 20px rgba(99, 102, 241, 0.15)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  background: '#000000',
                  minHeight: '260px'
                }}
              >
                <img
                  src={`${imageUrl}?v=${currentPage}`}
                  alt={`Slide ${currentPage} of ${selectedDoc}`}
                  style={{
                    width: '100%',
                    height: 'auto',
                    maxHeight: 'calc(100vh - 250px)',
                    objectFit: 'contain',
                    display: 'block'
                  }}
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
              </div>

              {/* Bottom Slide Strip & Controls Deck */}
              <div style={{
                width: '100%',
                maxWidth: '920px',
                marginTop: '14px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}>
                {/* Horizontal Clickable Slide Strip */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  overflowX: 'auto',
                  padding: '4px 2px',
                  scrollbarWidth: 'thin'
                }}>
                  {Array.from({ length: pageData?.total_pages || 1 }, (_, i) => i + 1).map((num) => (
                    <button
                      key={num}
                      onClick={() => setCurrentPage(num)}
                      style={{
                        minWidth: '32px',
                        height: '28px',
                        padding: '0 8px',
                        borderRadius: '6px',
                        border: num === currentPage ? '1px solid var(--accent-primary)' : '1px solid var(--border-subtle)',
                        background: num === currentPage ? 'var(--accent-primary)' : 'var(--btn-secondary-bg)',
                        color: num === currentPage ? '#ffffff' : 'var(--text-secondary)',
                        fontSize: '0.75rem',
                        fontWeight: num === currentPage ? 700 : 500,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        boxShadow: num === currentPage ? '0 0 10px rgba(99, 102, 241, 0.35)' : 'none',
                        transition: 'all 0.15s ease'
                      }}
                      title={`Go to Slide / Page ${num}`}
                    >
                      {num}
                    </button>
                  ))}
                </div>

                {/* Navigation Bar Controls */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '0.75rem',
                  color: 'var(--text-dim)'
                }}>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      onClick={handlePrevPage}
                      disabled={currentPage <= 1}
                      className="btn btn-secondary btn-sm"
                      style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                    >
                      <ChevronLeft size={13} />
                      <span>Previous</span>
                    </button>
                    <button
                      onClick={handleNextPage}
                      disabled={currentPage >= (pageData?.total_pages || 1)}
                      className="btn btn-secondary btn-sm"
                      style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                    >
                      <span>Next</span>
                      <ChevronRight size={13} />
                    </button>
                  </div>
                  <span>💡 Tip: Press <strong>←</strong> / <strong>→</strong> arrow keys to switch slides</span>
                </div>
              </div>

            </div>
          )}

        </div>



      </div>

    </div>
  );
}

