import React, { useState, useEffect, useRef } from 'react';
import { 
  MessageSquare, 
  FolderOpen, 
  Eye, 
  GitCompare, 
  BarChart3, 
  RefreshCw, 
  Server, 
  Database, 
  Cpu,
  ChevronDown
} from 'lucide-react';
import ThemeSelector from './ThemeSelector';

export default function Navbar({ activeTab, setActiveTab, health, onRefreshHealth, isRefreshing }) {
  const [showHealthMenu, setShowHealthMenu] = useState(false);
  const healthMenuRef = useRef(null);

  const tabs = [
    { id: 'chat', label: 'Chat Studio', icon: MessageSquare },
    { id: 'library', label: 'Document Library', icon: FolderOpen },
    { id: 'viewer', label: 'PDF & Slides', icon: Eye },
    { id: 'compare', label: 'Comparison Matrix', icon: GitCompare },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 }
  ];

  // Close health dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (healthMenuRef.current && !healthMenuRef.current.contains(e.target)) {
        setShowHealthMenu(false);
      }
    };
    if (showHealthMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showHealthMenu]);

  const isHealthy = health?.status === 'healthy';

  return (
    <header style={{
      height: '64px',
      borderBottom: '1px solid var(--border-subtle)',
      background: 'var(--bg-glass-elevated)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 20px',
      zIndex: 50,
      width: '100%',
      maxWidth: '100vw',
      boxSizing: 'border-box',
      transition: 'background 0.25s ease, border-color 0.25s ease'
    }}>

      {/* Brand Identity - Sleek & Compact */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '10px',
          background: 'var(--gradient-brand)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 14px rgba(99, 102, 241, 0.4)',
          fontSize: '1.15rem'
        }}>
          📚
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h1 style={{ 
            fontSize: '1rem', 
            fontWeight: 800, 
            letterSpacing: '-0.01em',
            background: 'var(--gradient-title)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            whiteSpace: 'nowrap'
          }}>
            RAG Assistant
          </h1>
          <span className="badge badge-indigo" style={{ padding: '2px 7px', fontSize: '0.65rem' }}>PRO</span>
        </div>
      </div>

      {/* Primary Tab Navigation */}
      <nav style={{ 
        display: 'flex', 
        gap: '4px', 
        background: 'var(--card-subtle-bg)', 
        padding: '3px 4px', 
        borderRadius: '12px', 
        border: '1px solid var(--border-subtle)',
        flexShrink: 0
      }}>
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
                gap: '7px',
                padding: '6px 13px',
                borderRadius: '8px',
                fontSize: '0.825rem',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                background: isActive ? 'var(--nav-tab-active-bg)' : 'transparent',
                color: isActive ? 'var(--nav-tab-active-text)' : 'var(--text-secondary)',
                boxShadow: isActive ? 'var(--nav-tab-active-shadow)' : 'none',
                whiteSpace: 'nowrap'
              }}
            >
              <Icon size={15} color={isActive ? 'var(--nav-tab-active-text)' : 'currentColor'} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Right Controls: Theme Selector & Consolidated Health Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
        
        {/* Background Theme Selector */}
        <ThemeSelector />

        {/* Consolidated System Health Status Pill */}
        <div style={{ position: 'relative' }} ref={healthMenuRef}>
          <button
            onClick={() => setShowHealthMenu(!showHealthMenu)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 12px',
              borderRadius: '9999px',
              border: '1px solid var(--border-medium)',
              background: 'rgba(255, 255, 255, 0.04)',
              color: 'var(--text-primary)',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: 'pointer',
              backdropFilter: 'blur(12px)',
              WebkitBackdropFilter: 'blur(12px)',
              transition: 'all 0.15s ease'
            }}
            title="System Diagnostics & LLM Status"
          >
            {/* Pulsing Status Dot */}
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: isHealthy ? '#10b981' : '#f43f5e',
              boxShadow: isHealthy ? '0 0 8px #10b981' : '0 0 8px #f43f5e',
              display: 'inline-block'
            }} />
            
            <span>Status</span>

            {/* Chunks count pill */}
            <span style={{
              fontSize: '0.7rem',
              padding: '1px 6px',
              borderRadius: '9999px',
              background: 'rgba(99, 102, 241, 0.18)',
              color: '#a5b4fc',
              fontWeight: 700
            }}>
              {health?.document_count || 0}
            </span>

            <ChevronDown size={12} color="var(--text-dim)" style={{ transform: showHealthMenu ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
          </button>

          {/* Diagnostic Popover */}
          {showHealthMenu && (
            <div 
              className="glass-panel animate-fade-in"
              style={{
                position: 'absolute',
                top: 'calc(100% + 8px)',
                right: 0,
                width: '280px',
                padding: '14px',
                background: 'var(--bg-sidebar)',
                border: '1px solid var(--border-glow)',
                borderRadius: '14px',
                boxShadow: '0 20px 40px rgba(0, 0, 0, 0.65), 0 0 25px rgba(99, 102, 241, 0.15)',
                zIndex: 100,
                backdropFilter: 'blur(24px)',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
                <span style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                  System Diagnostics
                </span>
                <button 
                  onClick={(e) => { e.stopPropagation(); onRefreshHealth(); }}
                  style={{ 
                    background: 'transparent', 
                    border: 'none', 
                    cursor: 'pointer', 
                    color: 'var(--text-secondary)',
                    padding: '3px',
                    borderRadius: '4px',
                    display: 'flex',
                    alignItems: 'center'
                  }}
                  title="Refresh Diagnostics"
                >
                  <RefreshCw size={13} className={isRefreshing ? 'pulse-indicator' : ''} />
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.8rem' }}>
                {/* FastAPI backend */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Server size={13} /> FastAPI Backend
                  </span>
                  <span style={{ color: isHealthy ? '#34d399' : '#fb7185', fontWeight: 600 }}>
                    {isHealthy ? 'Online' : 'Degraded'}
                  </span>
                </div>

                {/* ChromaDB Chunks */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Database size={13} /> ChromaDB Vectors
                  </span>
                  <span style={{ color: '#38bdf8', fontWeight: 600 }}>
                    {health?.document_count || 0} Chunks
                  </span>
                </div>

                {/* LLM Engine */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Cpu size={13} /> LLM Engine
                  </span>
                  <span style={{ color: health?.ollama_available ? '#a5b4fc' : '#fbbf24', fontWeight: 600 }}>
                    {health?.ollama_available ? 'Ollama (llama3:8b)' : 'Fallback'}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

      </div>
    </header>
  );
}
