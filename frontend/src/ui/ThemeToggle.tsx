import { useState } from 'react';

type Theme = 'night' | 'day';

const STORAGE_KEY = 'bv-theme';

function currentTheme(): Theme {
  const pinned = document.documentElement.dataset.theme;
  if (pinned === 'night' || pinned === 'day') return pinned;
  return window.matchMedia('(prefers-color-scheme: light)').matches
    ? 'day'
    : 'night';
}

/** Switches between Night and Day and remembers the choice on this device. */
export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(currentTheme);
  const next: Theme = theme === 'night' ? 'day' : 'night';

  const toggle = () => {
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // Storage unavailable: the choice lasts for this page view only.
    }
    setTheme(next);
  };

  return (
    <button
      type="button"
      className="nav-tab"
      onClick={toggle}
      aria-label={`Switch to ${next} theme`}
      title={`Switch to ${next} theme`}
    >
      {theme === 'night' ? '☾ Night' : '☀ Day'}
    </button>
  );
}
