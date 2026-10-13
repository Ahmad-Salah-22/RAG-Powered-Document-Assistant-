import React from 'react';
import { 
  MessageSquare, 
  FolderOpen, 
  Eye, 
  GitCompare, 
  BarChart3, 
  RefreshCw, 
  Server, 
  Database, 
  Cpu 
} from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, health, onRefreshHealth, isRefreshing }) {
  const tabs = [
    { id: 'chat', label: 'Chat Studio', icon: MessageSquare },
    { id: 'library', label: 'Document Library', icon: FolderOpen },
    { id: 'viewer', label: 'Visual PDF Viewer', icon: Eye },
    { id: 'compare', label: 'Comparison Matrix', icon: GitCompare },
    { id: 'analytics', label: 'Analytics & Ragas', icon: BarChart3 }
  ];

  return (
    <header style={{
      height: '68px',
      borderBottom: '1px solid var(--border-subtle)',
      background: 'rgba(11, 15, 25, 0.85)',
      backdropFilter: 'blur(20px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      zIndex: 50
    }}>
      {/* Brand Identity */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          background: 'var(--gradient-brand)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 15px rgba(99, 102, 241, 0.4)'
        }}>
          <span style={{ fontSize: '1.25rem' }}>📚</span>
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h1 style={{ 
              fontSize: '1.05rem', 
              fontWeight: 800, 
              background: 'linear-gradient(135deg, #ffffff 30%, #94a3b8 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              RAG Document Assistant
            </h1>
            <span className="badge badge-indigo">PRO STUDIO</span>
          </div>
          <p style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
            Hybrid SOTA Retrieval &amp; Agentic CRAG
          </p>
        </div>
      </div>

      {/* Primary Tab Navigation */}
      <nav style={{ display: 'flex', gap: '6px', background: 'rgba(255, 255, 255, 0.03)', padding: '4px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 14px',
                borderRadius: '8px',
                fontSize: '0.85rem',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                background: isActive ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(168, 85, 247, 0.15))' : 'transparent',
                color: isActive ? '#ffffff' : 'var(--text-secondary)',
                boxShadow: isActive ? 'inset 0 0 0 1px rgba(99, 102, 241, 0.5)' : 'none'
              }}
            >
              <Icon size={16} color={isActive ? '#818cf8' : 'currentColor'} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>

      {/* System Diagnostic Status Monitor */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {/* Backend API status */}
        <div 
          className="badge" 
          style={{ 
            background: health?.status === 'healthy' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(244, 63, 94, 0.1)',
            borderColor: health?.status === 'healthy' ? 'rgba(16, 185, 129, 0.25)' : 'rgba(244, 63, 94, 0.25)',
            color: health?.status === 'healthy' ? '#34d399' : '#fb7185',
            padding: '5px 9px'
          }}
          title={health?.status === 'healthy' ? 'FastAPI Backend Online' : 'FastAPI Degraded or Offline'}
        >
          <Server size={13} />
          <span>API: {health?.status === 'healthy' ? 'Online' : 'Degraded'}</span>
        </div>

        {/* Vectors Count */}
        <div 
          className="badge badge-cyan"
          style={{ padding: '5px 9px' }}
          title="Indexed Chunks in ChromaDB"
        >
          <Database size={13} />
          <span>{health?.document_count || 0} Chunks</span>
        </div>

        {/* Ollama LLM Status */}
        <div 
          className="badge"
          style={{ 
            background: health?.ollama_available ? 'rgba(99, 102, 241, 0.12)' : 'rgba(245, 158, 11, 0.12)',
            borderColor: health?.ollama_available ? 'rgba(99, 102, 241, 0.3)' : 'rgba(245, 158, 11, 0.3)',
            color: health?.ollama_available ? '#a5b4fc' : '#fbbf24',
            padding: '5px 9px'
          }}
          title={health?.ollama_available ? 'Ollama Daemon Active' : 'Ollama Offline (Extractive Fallback Active)'}
        >
          <Cpu size={13} />
          <span>LLM: {health?.ollama_available ? 'Ollama' : 'Fallback'}</span>
        </div>

        {/* Refresh Ping */}
        <button 
          onClick={onRefreshHealth}
          className="btn-icon"
          title="Refresh Diagnostic Status"
          style={{ cursor: 'pointer', border: 'none', background: 'transparent' }}
        >
          <RefreshCw size={15} className={isRefreshing ? 'pulse-indicator' : ''} />
        </button>
      </div>
    </header>
  );
}
