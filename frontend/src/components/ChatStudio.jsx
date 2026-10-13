import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Sparkles, 
  Plus, 
  Trash2, 
  Sliders, 
  BookOpen, 
  CheckCircle, 
  ChevronDown, 
  ChevronUp, 
  ExternalLink, 
  Copy, 
  Check, 
  Download, 
  Bot, 
  User, 
  Zap, 
  BrainCircuit, 
  Filter 
} from 'lucide-react';
import { submitQuery } from '../services/api';

export default function ChatStudio({ documents, onViewDocument }) {
  // Session State
  const [sessions, setSessions] = useState([
    { id: 'session-1', title: 'New Research Chat', messages: [] }
  ]);
  const [activeSessionId, setActiveSessionId] = useState('session-1');

  // RAG Configuration State
  const [promptMode, setPromptMode] = useState('academic');
  const [retrievalMode, setRetrievalMode] = useState('hybrid');
  const [topK, setTopK] = useState(4);
  const [enableReranker, setEnableReranker] = useState(true);
  const [agenticMode, setAgenticMode] = useState(true);
  const [queryExpansion, setQueryExpansion] = useState(false);
  const [selectedDocFilter, setSelectedDocFilter] = useState('');
  const [showConfig, setShowConfig] = useState(false);

  // Input & Query State
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState(null);

  const messagesEndRef = useRef(null);
  const activeSession = sessions.find(s => s.id === activeSessionId) || sessions[0];

  const dynamicSuggestions = React.useMemo(() => {
    if (!documents || documents.length === 0) {
      return [
        { category: 'Document Library', text: 'Upload your research papers or project documents in the Document Library to begin querying.' }
      ];
    }

    const suggestions = [];
    const docNames = documents.map(d => d.document_name.toLowerCase());

    // When Data Modeling documents are indexed
    if (docNames.some(n => n.includes('data_modeling') || n.includes('model'))) {
      suggestions.push(
        { category: 'Quality Criteria', text: 'What are the eight quality criteria of a good data model?' },
        { category: 'Review Checklist', text: 'What are the key questions and warning signs in the Quality Review Checklist?' },
        { category: 'Criteria Trade-offs', text: 'What are the conflicting objectives and trade-offs in data model quality criteria?' },
        { category: 'Architecture', text: 'Explain the three-schema architecture (conceptual, logical, physical) and why data modeling is a design activity.' }
      );
    }

    // When Data Discovery presentation is indexed
    if (docNames.some(n => n.includes('discovery'))) {
      suggestions.push(
        { category: 'Data Discovery', text: 'What are the core stages and methodologies of Data Discovery?' },
        { category: 'Executive Summary', text: 'Summarize the primary actionable takeaways and findings from Data Discovery.' }
      );
    }

    // Dynamic suggestions for any custom user-uploaded files
    documents.forEach(doc => {
      const lower = doc.document_name.toLowerCase();
      if (!lower.includes('data_modeling') && !lower.includes('discovery')) {
        suggestions.push(
          { category: doc.document_name.slice(0, 16), text: `What are the core criteria and methodologies defined in ${doc.document_name}?` },
          { category: 'Executive Summary', text: `Summarize the key takeaways and architectural principles from ${doc.document_name}.` }
        );
      }
    });

    return suggestions.slice(0, 6);
  }, [documents]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeSession?.messages, isLoading]);

  const createNewSession = () => {
    const newId = `session-${Date.now()}`;
    const newSession = {
      id: newId,
      title: `Chat ${sessions.length + 1}`,
      messages: []
    };
    setSessions([newSession, ...sessions]);
    setActiveSessionId(newId);
  };

  const deleteSession = (e, id) => {
    e.stopPropagation();
    if (sessions.length <= 1) {
      setSessions([{ id: 'session-1', title: 'New Research Chat', messages: [] }]);
      setActiveSessionId('session-1');
      return;
    }
    const filtered = sessions.filter(s => s.id !== id);
    setSessions(filtered);
    if (activeSessionId === id) {
      setActiveSessionId(filtered[0].id);
    }
  };

  const handleSend = async (questionText = inputValue) => {
    const textToSend = questionText.trim();
    if (!textToSend || isLoading) return;

    setInputValue('');

    const userMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    // Update active session with user message
    const updatedMessages = [...activeSession.messages, userMessage];
    setSessions(sessions.map(s => {
      if (s.id === activeSessionId) {
        return {
          ...s,
          title: s.messages.length === 0 ? textToSend.slice(0, 32) + '...' : s.title,
          messages: updatedMessages
        };
      }
      return s;
    }));

    setIsLoading(true);

    try {
      // Format chat history for backend
      const historyPayload = updatedMessages
        .slice(-6)
        .map(m => ({ role: m.role, content: m.content }));

      const payload = {
        question: textToSend,
        top_k: topK,
        retrieval_mode: retrievalMode,
        enable_reranker: enableReranker,
        agentic_mode: agenticMode,
        query_expansion: queryExpansion,
        system_prompt_mode: promptMode,
        document_filter: selectedDocFilter ? [selectedDocFilter] : null,
        chat_history: historyPayload
      };

      const response = await submitQuery(payload);

      const assistantMessage = {
        id: `msg-resp-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        sources: response.sources || [],
        modelUsed: response.model_used,
        latencyMs: response.latency_ms,
        retrievalLatency: response.retrieval_latency_ms,
        generationLatency: response.generation_latency_ms,
        fallbackUsed: response.fallback_used,
        agenticActive: response.agentic_active,
        intentType: response.intent_type,
        confidenceScore: response.confidence_score,
        reasoningSteps: response.reasoning_steps || [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setSessions(prev => prev.map(s => {
        if (s.id === activeSessionId) {
          return { ...s, messages: [...s.messages, assistantMessage] };
        }
        return s;
      }));

    } catch (err) {
      const errorMessage = {
        id: `msg-err-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ Error executing query: ${err.message}. Please check if the FastAPI backend is running at http://localhost:8000.`,
        sources: [],
        isError: true,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setSessions(prev => prev.map(s => {
        if (s.id === activeSessionId) {
          return { ...s, messages: [...s.messages, errorMessage] };
        }
        return s;
      }));
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const exportChatMarkdown = () => {
    if (!activeSession.messages.length) return;
    const md = activeSession.messages.map(m => {
      return `### ${m.role === 'user' ? '👤 User' : '🤖 Assistant'} (${m.timestamp})\n\n${m.content}\n\n`;
    }).join('---\n\n');
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${activeSession.title.replace(/[^a-z0-9]/gi, '_')}.md`;
    a.click();
  };

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 68px)', width: '100%', overflow: 'hidden' }}>
      
      {/* Sidebar: Conversation Sessions & RAG Settings */}
      <aside style={{
        width: '300px',
        borderRight: '1px solid var(--border-subtle)',
        background: 'var(--bg-sidebar)',
        display: 'flex',
        flexDirection: 'column',
        padding: '16px',
        gap: '16px'
      }}>
        {/* Action Header */}
        <div style={{ display: 'flex', gap: '8px' }}>
          <button 
            onClick={createNewSession}
            className="btn btn-primary"
            style={{ flex: 1, fontSize: '0.825rem' }}
          >
            <Plus size={15} />
            <span>New Chat</span>
          </button>
          <button
            onClick={() => setShowConfig(!showConfig)}
            className={`btn ${showConfig ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '8px' }}
            title="Toggle RAG Tuning Drawer"
          >
            <Sliders size={15} />
          </button>
        </div>

        {/* Collapsible Tuning Drawer */}
        {showConfig && (
          <div className="glass-panel" style={{ padding: '12px', fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ fontWeight: 700, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Zap size={14} color="#818cf8" />
              <span>RAG Architecture Controls</span>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.725rem', color: 'var(--text-muted)', marginBottom: '3px' }}>System Prompt Mode</label>
              <select value={promptMode} onChange={e => setPromptMode(e.target.value)} style={{ padding: '6px 8px', fontSize: '0.775rem' }}>
                <option value="academic">Academic Research</option>
                <option value="concise">Executive Concise</option>
                <option value="detailed">Detailed Tutorial</option>
                <option value="summary">Executive Summary</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.725rem', color: 'var(--text-muted)', marginBottom: '3px' }}>Retrieval Engine</label>
              <select value={retrievalMode} onChange={e => setRetrievalMode(e.target.value)} style={{ padding: '6px 8px', fontSize: '0.775rem' }}>
                <option value="hybrid">Hybrid (Dense + BM25 RRF)</option>
                <option value="dense">Dense Semantic Vectors</option>
                <option value="bm25">BM25 Okapi Lexical</option>
              </select>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.725rem', color: 'var(--text-muted)' }}>
                <span>Top-K Context Chunks</span>
                <span style={{ color: '#818cf8', fontWeight: 600 }}>{topK}</span>
              </div>
              <input 
                type="range" 
                min="1" 
                max="8" 
                value={topK} 
                onChange={e => setTopK(Number(e.target.value))} 
                style={{ width: '100%', accentColor: 'var(--accent-primary)', marginTop: '4px' }}
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', paddingTop: '4px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.75rem' }}>
                <input type="checkbox" checked={enableReranker} onChange={e => setEnableReranker(e.target.checked)} style={{ width: 'auto' }} />
                <span>Cross-Encoder Re-Ranking</span>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.75rem' }}>
                <input type="checkbox" checked={agenticMode} onChange={e => setAgenticMode(e.target.checked)} style={{ width: 'auto' }} />
                <span>Agentic CRAG Reasoning</span>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.75rem' }}>
                <input type="checkbox" checked={queryExpansion} onChange={e => setQueryExpansion(e.target.checked)} style={{ width: 'auto' }} />
                <span>Semantic Query Expansion</span>
              </label>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.725rem', color: 'var(--text-muted)', marginBottom: '3px' }}>Filter by Document</label>
              <select value={selectedDocFilter} onChange={e => setSelectedDocFilter(e.target.value)} style={{ padding: '6px 8px', fontSize: '0.775rem' }}>
                <option value="">All Indexed Documents</option>
                {documents?.map(d => (
                  <option key={d.document_name} value={d.document_name}>{d.document_name}</option>
                ))}
              </select>
            </div>
          </div>
        )}

        {/* Conversation Sessions List */}
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ fontSize: '0.725rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em', padding: '0 4px' }}>
            Chat History
          </div>
          {sessions.map(s => {
            const isActive = s.id === activeSessionId;
            return (
              <div
                key={s.id}
                onClick={() => setActiveSessionId(s.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '9px 12px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  background: isActive ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                  border: `1px solid ${isActive ? 'rgba(99, 102, 241, 0.3)' : 'transparent'}`,
                  color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                  fontSize: '0.825rem',
                  transition: 'all 0.15s ease'
                }}
              >
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '200px' }}>
                  {s.title}
                </span>
                <button
                  onClick={(e) => deleteSession(e, s.id)}
                  style={{ background: 'transparent', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', padding: '2px' }}
                  title="Delete Chat"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            );
          })}
        </div>

        {/* Footer info */}
        <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.725rem', color: 'var(--text-dim)' }}>{documents?.length || 0} Docs Active</span>
          <button 
            onClick={exportChatMarkdown}
            className="btn btn-secondary btn-sm"
            title="Export conversation to Markdown"
          >
            <Download size={13} />
            <span>Export</span>
          </button>
        </div>
      </aside>

      {/* Main Chat Canvas */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', position: 'relative' }}>
        
        {/* Messages Scroll Area */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Welcome Screen & Prompt Library if no messages */}
          {activeSession.messages.length === 0 && (
            <div className="animate-fade-in" style={{ margin: 'auto', maxWidth: '680px', textAlign: 'center', padding: '40px 20px' }}>
              <div style={{
                width: '64px',
                height: '64px',
                borderRadius: '18px',
                background: 'var(--gradient-brand)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 20px',
                boxShadow: '0 0 30px rgba(99, 102, 241, 0.4)'
              }}>
                <Sparkles size={32} color="#ffffff" />
              </div>
              <h2 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '8px' }}>
                Ask your documents anything
              </h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: '28px' }}>
                Hybrid SOTA dense vector + BM25 retrieval with deep cross-encoder re-ranking and auditable page-level citations.
              </p>

              {/* Categorized Prompt Suggestions */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', textAlign: 'left' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.775rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  <span>Recommended Questions</span>
                  <span style={{ fontSize: '0.7rem', color: '#818cf8', textTransform: 'none', fontWeight: 500 }}>
                    Grounding from {documents?.length || 0} active project file{documents?.length === 1 ? '' : 's'}
                  </span>
                </div>
                {dynamicSuggestions.map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(item.text)}
                    className="glass-panel"
                    style={{
                      padding: '12px 16px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      border: '1px solid var(--border-subtle)',
                      background: 'rgba(255, 255, 255, 0.02)',
                      textAlign: 'left'
                    }}
                  >
                    <div>
                      <span className="badge badge-indigo" style={{ marginRight: '10px' }}>{item.category}</span>
                      <span style={{ fontSize: '0.875rem', color: 'var(--text-primary)' }}>{item.text}</span>
                    </div>
                    <Send size={14} color="#818cf8" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Conversation Exchange */}
          {activeSession.messages.map((msg) => (
            <div 
              key={msg.id} 
              className="animate-fade-in"
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start',
                width: '100%'
              }}
            >
              {/* Message Header */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                {msg.role === 'user' ? (
                  <>
                    <span>You</span>
                    <div style={{ width: '22px', height: '22px', borderRadius: '50%', background: 'rgba(99, 102, 241, 0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <User size={13} color="#818cf8" />
                    </div>
                  </>
                ) : (
                  <>
                    <div style={{ width: '22px', height: '22px', borderRadius: '50%', background: 'rgba(6, 182, 212, 0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Bot size={13} color="#22d3ee" />
                    </div>
                    <span>Assistant</span>
                    {msg.latencyMs && (
                      <span className="badge badge-cyan" style={{ fontSize: '0.675rem' }}>
                        {msg.latencyMs}ms ({msg.modelUsed || 'Ollama'})
                      </span>
                    )}
                  </>
                )}
                <span>{msg.timestamp}</span>
              </div>

              {/* Message Bubble */}
              <div 
                style={{
                  maxWidth: msg.role === 'user' ? '75%' : '90%',
                  padding: '16px 20px',
                  borderRadius: '16px',
                  background: msg.role === 'user' 
                    ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(79, 70, 229, 0.2))' 
                    : 'var(--bg-card)',
                  border: `1px solid ${msg.role === 'user' ? 'rgba(99, 102, 241, 0.4)' : 'var(--border-subtle)'}`,
                  backdropFilter: 'blur(16px)',
                  boxShadow: 'var(--shadow-card)',
                  lineHeight: 1.65,
                  fontSize: '0.925rem',
                  whiteSpace: 'pre-wrap'
                }}
              >
                {/* Agentic Reasoning Trace Accordion */}
                {msg.agenticActive && msg.reasoningSteps && (
                  <details style={{ marginBottom: '14px', background: 'rgba(0, 0, 0, 0.3)', padding: '10px 14px', borderRadius: '10px', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
                    <summary style={{ cursor: 'pointer', fontWeight: 600, color: '#818cf8', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem' }}>
                      <BrainCircuit size={15} />
                      <span>Agentic CRAG Reasoning Trace (Intent: {msg.intentType || 'Factual Lookup'})</span>
                    </summary>
                    <div style={{ marginTop: '10px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      {msg.confidenceScore && (
                        <div style={{ marginBottom: '8px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                            <span>Retrieval Grounding Confidence:</span>
                            <span style={{ fontWeight: 700, color: '#34d399' }}>{msg.confidenceScore}%</span>
                          </div>
                          <div style={{ height: '5px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div style={{ width: `${msg.confidenceScore}%`, height: '100%', background: 'linear-gradient(90deg, #6366f1, #10b981)' }} />
                          </div>
                        </div>
                      )}
                      <ul style={{ paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        {msg.reasoningSteps.map((step, sIdx) => (
                          <li key={sIdx}>
                            <strong style={{ color: 'var(--text-primary)' }}>{step.step}:</strong> {step.detail}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </details>
                )}

                {/* Answer Content */}
                <div>{msg.content}</div>

                {/* Source Citations Shelf */}
                {msg.sources && msg.sources.length > 0 && (
                  <div style={{ marginTop: '16px', paddingTop: '14px', borderTop: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <BookOpen size={13} color="#22d3ee" />
                      <span>Verified Auditable Sources ({msg.sources.length})</span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '10px' }}>
                      {msg.sources.map((src, srcIdx) => (
                        <div 
                          key={srcIdx}
                          style={{
                            background: 'rgba(15, 23, 42, 0.6)',
                            border: '1px solid rgba(255, 255, 255, 0.08)',
                            borderRadius: '10px',
                            padding: '10px',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '6px'
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontWeight: 600, fontSize: '0.8rem', color: '#f1f5f9', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '170px' }}>
                              {src.document}
                            </span>
                            <span className="badge badge-indigo" style={{ fontSize: '0.7rem' }}>
                              Page {src.page}
                            </span>
                          </div>

                          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                            "{src.snippet}"
                          </p>

                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto', paddingTop: '4px' }}>
                            {src.confidence_percent && (
                              <span style={{ fontSize: '0.7rem', color: '#34d399', fontWeight: 600 }}>
                                {src.confidence_percent}% confidence
                              </span>
                            )}
                            <button
                              onClick={() => onViewDocument(src.document, src.page)}
                              className="btn btn-secondary btn-sm"
                              style={{ padding: '3px 7px', fontSize: '0.7rem', color: '#818cf8', borderColor: 'rgba(99, 102, 241, 0.3)' }}
                              title="Open verified page in Visual PDF Viewer"
                            >
                              <ExternalLink size={11} />
                              <span>View Page</span>
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Footer Controls */}
                {msg.role === 'assistant' && (
                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px', gap: '8px' }}>
                    <button
                      onClick={() => copyToClipboard(msg.content, msg.id)}
                      className="btn-icon"
                      style={{ border: 'none', background: 'transparent', cursor: 'pointer', padding: '4px' }}
                      title="Copy Answer"
                    >
                      {copiedId === msg.id ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Typing Indicator */}
          {isLoading && (
            <div className="animate-fade-in" style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'rgba(99, 102, 241, 0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Bot size={14} color="#818cf8" className="pulse-indicator" />
              </div>
              <span>Searching vector database, cross-encoding context &amp; generating grounded response...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div style={{
          padding: '16px 32px 24px',
          background: 'linear-gradient(to top, var(--bg-app) 80%, transparent)',
          borderTop: '1px solid var(--border-subtle)'
        }}>
          <form 
            onSubmit={(e) => { e.preventDefault(); handleSend(); }}
            style={{
              display: 'flex',
              alignItems: 'center',
              background: 'var(--bg-input)',
              border: '1px solid var(--border-medium)',
              borderRadius: '14px',
              padding: '6px 8px 6px 16px',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.4)',
              transition: 'border-color 0.2s ease'
            }}
          >
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask anything about your uploaded documents..."
              disabled={isLoading}
              style={{
                flex: 1,
                border: 'none',
                background: 'transparent',
                padding: '8px 0',
                color: 'var(--text-primary)',
                fontSize: '0.95rem',
                outline: 'none',
                boxShadow: 'none'
              }}
            />
            <button
              type="submit"
              disabled={isLoading || !inputValue.trim()}
              className="btn btn-primary"
              style={{
                padding: '9px 18px',
                borderRadius: '10px',
                opacity: (!inputValue.trim() || isLoading) ? 0.5 : 1,
                cursor: (!inputValue.trim() || isLoading) ? 'not-allowed' : 'pointer'
              }}
            >
              <Send size={16} />
              <span>Ask</span>
            </button>
          </form>
          <div style={{ textAlign: 'center', marginTop: '8px', fontSize: '0.725rem', color: 'var(--text-dim)' }}>
            Grounded local RAG • Strict anti-hallucination citations • Privacy-first local execution
          </div>
        </div>

      </main>
    </div>
  );
}
