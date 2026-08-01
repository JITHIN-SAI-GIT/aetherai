import { useCallback, useEffect, useState } from 'react';
import type { AccentColor, Settings } from '@/types';
import { applyAccent } from '@/utils/accent';

const STORAGE_KEY = 'nova-settings';

const defaultSettings: Settings = {
  accent: 'teal',
  language: 'English',
  temperature: 0.7,
  model: 'nova-pro',
  memory: true,
};

export function useSettings() {
  const [settings, setSettings] = useState<Settings>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        return { ...defaultSettings, ...JSON.parse(stored) } as Settings;
      } catch {
        // fall through
      }
    }
    return defaultSettings;
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    applyAccent(settings.accent as AccentColor);
  }, [settings]);

  const update = useCallback(<K extends keyof Settings>(key: K, value: Settings[K]) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  }, []);

  const reset = useCallback(() => setSettings(defaultSettings), []);

  return { settings, update, reset };
}
