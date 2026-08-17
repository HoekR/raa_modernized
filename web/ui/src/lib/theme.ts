import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export type ColorTheme = 'archive' | 'copper' | 'green';

export const THEME_OPTIONS: { id: ColorTheme; label: string }[] = [
  { id: 'archive', label: 'Archiefblauw (B)' },
  { id: 'copper', label: 'Koper / Goetgevonden (A)' },
  { id: 'green', label: 'Erfgoedgroen (C)' },
];

const STORAGE_KEY = 'raa-color-theme';

function readStored(): ColorTheme {
  if (!browser) return 'archive';
  const v = localStorage.getItem(STORAGE_KEY);
  if (v === 'copper' || v === 'green' || v === 'archive') return v;
  return 'archive';
}

function applyTheme(id: ColorTheme) {
  if (!browser) return;
  document.documentElement.dataset.theme = id;
  localStorage.setItem(STORAGE_KEY, id);
}

export const colorTheme = writable<ColorTheme>(readStored());

if (browser) {
  applyTheme(readStored());
  colorTheme.subscribe(applyTheme);
}
