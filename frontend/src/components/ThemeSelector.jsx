import React, { useState, useEffect, useRef } from 'react';
import { Palette, Check, Sparkles, ChevronDown } from 'lucide-react';

export const THEMES = [
  {
    id: 'cosmic',
    name: 'Cosmic Midnight',
    tagline: 'Deep Obsidian & Indigo Nebula',
    color1: '#6366f1',
    color2: '#06b6d4',
    bg: '#080b12',
    accent: '#818cf8',
    isDark: true
  },
  {
    id: 'cyberpunk',
    name: 'Cyberpunk Neon',
    tagline: 'Ultraviolet & Hot Fuchsia',
    color1: '#ec4899',
    color2: '#a855f7',
    bg: '#090414',
    accent: '#f472b6',
    isDark: true
  },
  {
    id: 'emerald',
    name: 'Emerald Matrix',
    tagline: 'Bioluminescent Mint & Jade',
    color1: '#10b981',
    color2: '#06b6d4',
    bg: '#030f0c',
    accent: '#34d399',
    isDark: true
  },
  {
    id: 'ocean',
    name: 'Oceanic Abyss',
    tagline: 'Deep Sea Navy & Vibrant Cyan',
    color1: '#06b6d4',
    color2: '#3b82f6',
    bg: '#040b17',
    accent: '#38bdf8',
    isDark: true
  },
  {
    id: 'sunset',
    name: 'Solar Ember',
    tagline: 'Sunset Amber & Volcanic Glow',
    color1: '#f59e0b',
    color2: '#ea580c',
    bg: '#120805',
    accent: '#fbbf24',
    isDark: true
  },
  {
    id: 'obsidian',
    name: 'Obsidian Stealth',
    tagline: 'Pure OLED Carbon & Platinum',
    color1: '#a1a1aa',
    color2: '#e4e4e7',
    bg: '#000000',
    accent: '#cbd5e1',
    isDark: true
  },
  {
    id: 'nordic',
    name: 'Nordic Frost',
    tagline: 'Frosted Porcelain Light Mode',
    color1: '#4f46e5',
    color2: '#0284c7',
    bg: '#f1f5f9',
    accent: '#4f46e5',
    isDark: false
  }
];

export default function ThemeSelector() {
  const [isOpen, setIsOpen] = useState(false);
  const [currentTheme, setCurrentTheme] = useState(() => {
    return localStorage.getItem('rag_studio_theme') || 'cosmic';
  });
  const dropdownRef = useRef(null);

  // Apply theme to document element
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', currentTheme);
    localStorage.setItem('rag_studio_theme', currentTheme);
  }, [currentTheme]);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const activeThemeObj = THEMES.find(t => t.id === currentTheme) || THEMES[0];

  return (
    <div style={{ position: 'relative' }} ref={dropdownRef}>
      {/* Compact Navbar Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '7px',
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
        title={`Theme: ${activeThemeObj.name} (Click to switch)`}
      >
        {/* Animated Gradient Dot */}
        <span style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          background: `linear-gradient(135deg, ${activeThemeObj.color1}, ${activeThemeObj.color2})`,
          boxShadow: `0 0 8px ${activeThemeObj.color1}`,
          display: 'inline-block'
        }} />

        <Palette size={13} color="var(--text-secondary)" />
        <span>Theme</span>
        <ChevronDown size={12} color="var(--text-dim)" style={{ transform: isOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div 
          className="glass-panel animate-fade-in"
          style={{
            position: 'absolute',
            top: 'calc(100% + 10px)',
            right: 0,
            width: '290px',
            padding: '12px',
            background: 'var(--bg-sidebar)',
            border: '1px solid var(--border-glow)',
            borderRadius: '16px',
            boxShadow: '0 20px 45px rgba(0, 0, 0, 0.65), 0 0 30px rgba(99, 102, 241, 0.15)',
            zIndex: 100,
            backdropFilter: 'blur(24px)'
          }}
        >
          {/* Header */}
          <div style={{ padding: '6px 8px 10px', borderBottom: '1px solid var(--border-subtle)', marginBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-primary)', fontWeight: 700, fontSize: '0.85rem' }}>
              <Sparkles size={14} color="var(--accent-primary)" />
              <span>Studio Background Themes</span>
            </div>
            <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px', margin: 0 }}>
              Curated visual palettes &amp; glowing ambiances
            </p>
          </div>

          {/* Theme Options List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxHeight: '360px', overflowY: 'auto' }}>
            {THEMES.map((theme) => {
              const isSelected = theme.id === currentTheme;
              return (
                <button
                  key={theme.id}
                  onClick={() => {
                    setCurrentTheme(theme.id);
                    setIsOpen(false);
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 10px',
                    borderRadius: '10px',
                    border: isSelected ? `1px solid ${theme.color1}` : '1px solid transparent',
                    background: isSelected ? 'rgba(255, 255, 255, 0.08)' : 'transparent',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.15s ease',
                    width: '100%'
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected) e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) e.currentTarget.style.background = 'transparent';
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    {/* Color Swatch Circle */}
                    <div style={{
                      width: '26px',
                      height: '26px',
                      borderRadius: '8px',
                      background: `linear-gradient(135deg, ${theme.color1}, ${theme.color2})`,
                      boxShadow: isSelected ? `0 0 12px ${theme.color1}` : '0 2px 6px rgba(0,0,0,0.4)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0
                    }}>
                      <div style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        background: theme.bg,
                        border: '1px solid rgba(255,255,255,0.4)'
                      }} />
                    </div>

                    <div>
                      <div style={{
                        fontSize: '0.8rem',
                        fontWeight: 700,
                        color: isSelected ? theme.accent : 'var(--text-primary)'
                      }}>
                        {theme.name}
                      </div>
                      <div style={{ fontSize: '0.675rem', color: 'var(--text-muted)' }}>
                        {theme.tagline}
                      </div>
                    </div>
                  </div>

                  {isSelected && (
                    <div style={{
                      width: '18px',
                      height: '18px',
                      borderRadius: '50%',
                      background: theme.color1,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: `0 0 8px ${theme.color1}`
                    }}>
                      <Check size={11} color="#ffffff" strokeWidth={3} />
                    </div>
                  )}
                </button>
              );
            })}
          </div>

        </div>
      )}
    </div>
  );
}
