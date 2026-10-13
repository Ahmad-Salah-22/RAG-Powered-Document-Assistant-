import React, { useState } from 'react';
import { GitCompare, BookOpen, Sparkles, ExternalLink, ArrowRight, Layers } from 'lucide-react';
import { submitComparison } from '../services/api';

export default function ComparisonMatrix({ documents, onViewDocument }) {
  const [docA, setDocA] = useState(documents[0]?.document_name || '');
  const [docB, setDocB] = useState(documents[1]?.document_name || documents[0]?.document_name || '');
  const [topic, setTopic] = useState('Core concepts, methodologies, key findings, and practical implications');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleRunComparison = async () => {
    if (!docA || !docB) return;
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await submitComparison({
        doc_a: docA,
        doc_b: docB,
        comparison_topic: topic
      });
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ padding: '32px 48px', height: 'calc(100vh - 68px)', overflowY: 'auto' }}>
      
      {/* Title */}
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Multi-Document Comparative Analysis Studio</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Simultaneous dual-corpus RAG retrieval to construct side-by-side comparative matrices with auditable cross-references.
        </p>
      </div>

      {/* Control Card */}
      <div className="glass-panel" style={{ padding: '24px', marginBottom: '28px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: '16px', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--accent-primary)', marginBottom: '6px' }}>
              Document A
            </label>
            <select value={docA} onChange={(e) => setDocA(e.target.value)} style={{ width: '100%' }}>
              {documents.map((d) => (
                <option key={d.document_name} value={d.document_name}>{d.document_name}</option>
              ))}
            </select>
          </div>

          <div style={{ paddingTop: '20px', color: 'var(--text-dim)' }}>
            <ArrowRight size={20} />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--accent-cyan)', marginBottom: '6px' }}>
              Document B
            </label>
            <select value={docB} onChange={(e) => setDocB(e.target.value)} style={{ width: '100%' }}>
              {documents.map((d) => (
                <option key={d.document_name} value={d.document_name}>{d.document_name}</option>
              ))}
            </select>
          </div>
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
            Comparison Focus / Research Question
          </label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g., Performance trade-offs, algorithms, and practical applications"
          />
        </div>

        <button
          onClick={handleRunComparison}
          disabled={isLoading || !docA || !docB}
          className="btn btn-primary"
          style={{ width: '100%', padding: '12px' }}
        >
          <GitCompare size={16} />
          <span>{isLoading ? 'Executing Comparative Retrieval & Matrix Synthesis...' : 'Run Comparative Analysis Matrix'}</span>
        </button>
      </div>

      {/* Error state */}
      {error && (
        <div className="glass-panel" style={{ padding: '16px', color: 'var(--accent-rose)', border: '1px solid rgba(244, 63, 94, 0.3)', marginBottom: '24px' }}>
          ⚠️ Error during comparison: {error}
        </div>
      )}

      {/* Results View */}
      {result && (
        <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Synthesis Card */}
          <div className="glass-panel" style={{ padding: '28px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={18} color="#818cf8" />
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Comparative Synthesis Matrix</h3>
              </div>
              <span className="badge badge-cyan">{result.latency_ms}ms total</span>
            </div>

            <div style={{ fontSize: '0.925rem', lineHeight: 1.7, color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>
              {result.synthesis}
            </div>
          </div>

          {/* Dual Sources Citations Breakdown */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            
            {/* Sources for Document A */}
            <div className="glass-panel" style={{ padding: '20px' }}>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--accent-primary)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <BookOpen size={14} />
                <span>Verified Citations: {result.doc_a} ({result.sources_a?.length || 0})</span>
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {result.sources_a?.map((s, idx) => (
                  <div key={idx} style={{ background: 'var(--card-subtle-bg)', border: '1px solid var(--border-subtle)', padding: '10px', borderRadius: '8px', fontSize: '0.8rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span className="badge badge-indigo">Page {s.page}</span>
                      <button onClick={() => onViewDocument(s.document, s.page)} className="btn btn-secondary btn-sm" style={{ padding: '2px 6px', fontSize: '0.675rem' }}>
                        View Page
                      </button>
                    </div>
                    <p style={{ color: 'var(--text-muted)' }}>"{s.snippet}"</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Sources for Document B */}
            <div className="glass-panel" style={{ padding: '20px' }}>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--accent-cyan)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <BookOpen size={14} />
                <span>Verified Citations: {result.doc_b} ({result.sources_b?.length || 0})</span>
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {result.sources_b?.map((s, idx) => (
                  <div key={idx} style={{ background: 'var(--card-subtle-bg)', border: '1px solid var(--border-subtle)', padding: '10px', borderRadius: '8px', fontSize: '0.8rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span className="badge badge-cyan">Page {s.page}</span>
                      <button onClick={() => onViewDocument(s.document, s.page)} className="btn btn-secondary btn-sm" style={{ padding: '2px 6px', fontSize: '0.675rem' }}>
                        View Page
                      </button>
                    </div>
                    <p style={{ color: 'var(--text-muted)' }}>"{s.snippet}"</p>
                  </div>
                ))}
              </div>
            </div>

          </div>

        </div>
      )}

    </div>
  );
}
