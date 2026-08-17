import { derived, writable } from 'svelte/store';

export type PeriodCount = { key: string; label: string; count: number };

/** Selected period key, or `"all"` for overall mode. */
export const periodKey = writable<string>('republiek');

export const periodMode = derived(periodKey, (k) => (k === 'all' ? 'overall' : 'scoped'));

export const periodParam = derived(periodKey, (k) => (k === 'all' ? null : k));

export const PAGE_SIZE = 100;
export const MAX_CHIPS = 5;

export type SuggestItem = { id: number; naam: string };

export type SearchResponse = {
  hits: Record<string, unknown>[];
  total: number;
  facets?: Record<string, FacetValue[]>;
};

export type FacetValue = { key: string; label: string; count: number };

export type BrowseResponse = {
  hits: Record<string, unknown>[];
  total: number;
  letter: string;
  letters: { letter: string; count: number }[];
};
