"use client";
import { useEffect, useState } from 'react';

/**
 * Simple theme toggle that adds/removes the `dark` class on <html>
 * Persists choice to localStorage (key: 'theme') where value is 'dark' or 'light'.
 */
export default function ThemeToggle() {
  const [isDark, setIsDark] = useState<boolean | null>(null);

  useEffect(() => {
    // On mount, read preference
    const stored = typeof window !== 'undefined' ? window.localStorage.getItem('theme') : null;
    if (stored === 'dark') {
      document.documentElement.classList.add('dark');
      setIsDark(true);
    } else if (stored === 'light') {
      document.documentElement.classList.remove('dark');
      setIsDark(false);
    } else {
      // No stored preference, respect system preference
      const prefers = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      if (prefers) {
        document.documentElement.classList.add('dark');
        setIsDark(true);
      } else {
        document.documentElement.classList.remove('dark');
        setIsDark(false);
      }
    }
  }, []);

  const toggle = () => {
    const newDark = !isDark;
    if (newDark) {
      document.documentElement.classList.add('dark');
      window.localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      window.localStorage.setItem('theme', 'light');
    }
    setIsDark(newDark);
  };

  return (
    <button
      aria-pressed={!!isDark}
      onClick={toggle}
      className="inline-flex items-center gap-2 rounded-md px-3 py-1 text-sm font-medium border border-transparent hover:shadow-sm"
      style={{
        background: 'transparent',
      }}
    >
      <span className="sr-only">Toggle theme</span>
      {isDark ? (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" fill="var(--color-accent)" />
        </svg>
      ) : (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="12" cy="12" r="5" fill="var(--color-primary)" />
        </svg>
      )}
      <span className="hidden sm:inline text-primary">{isDark ? 'Dark' : 'Light'}</span>
    </button>
  );
}
