'use client';
import { useState, useEffect } from 'react';
import { Sun, Moon } from 'lucide-react';

export default function ThemeToggle() {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  useEffect(() => {
    const stored = localStorage.getItem('theme') as 'dark' | 'light' | null;
    if (stored) {
      setTheme(stored);
      document.documentElement.setAttribute('data-theme', stored);
    }
  }, []);

  function toggle() {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem('theme', next);
    document.documentElement.setAttribute('data-theme', next);
  }

  return (
    <button
      onClick={toggle}
      aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
      className="p-2 rounded-[6px] border transition-colors"
      style={{
        borderColor: 'var(--border)',
        background: 'var(--surface)',
      }}
      onMouseEnter={(e) =>
        (e.currentTarget.style.borderColor = 'var(--border-strong)')
      }
      onMouseLeave={(e) =>
        (e.currentTarget.style.borderColor = 'var(--border)')
      }
    >
      {theme === 'dark' ? (
        <Sun size={16} style={{ color: 'var(--fg-muted)' }} />
      ) : (
        <Moon size={16} style={{ color: 'var(--fg-muted)' }} />
      )}
    </button>
  );
}
