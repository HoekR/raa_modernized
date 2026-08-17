import { derived, writable } from 'svelte/store';
import type { TimelineMeta, YearCount } from './yearHistogram';

export type PeriodCount = { key: string; label: string; count: number };

export const ALL_PERIODS_LABEL = 'Alle perioden (1428–1861)';

export type PeriodMode = 'overall' | 'scoped';

/** Selected period key, or `"all"` for overall mode. */
export const periodKey = writable<string>('republiek');

export const periodMode = derived(periodKey, (k): PeriodMode => (k === 'all' ? 'overall' : 'scoped'));

export const periodParam = derived(periodKey, (k) => (k === 'all' ? null : k));

export const PAGE_SIZE = 100;
export const PAGE_SIZE_OPTIONS = [20, 50, 100] as const;

const PAGE_SIZE_STORAGE_KEY = 'raa-page-size';

function readStoredPageSize(): number {
  if (typeof localStorage === 'undefined') return PAGE_SIZE;
  try {
    const raw = localStorage.getItem(PAGE_SIZE_STORAGE_KEY);
    if (!raw) return PAGE_SIZE;
    const n = Number(raw);
    return (PAGE_SIZE_OPTIONS as readonly number[]).includes(n) ? n : PAGE_SIZE;
  } catch {
    return PAGE_SIZE;
  }
}

/** Results per page (shared across search/browse pages). */
export const pageSize = writable(readStoredPageSize());

if (typeof window !== 'undefined') {
  pageSize.subscribe((v) => {
    try {
      localStorage.setItem(PAGE_SIZE_STORAGE_KEY, String(v));
    } catch {
      /* ignore quota errors */
    }
  });
}

export const MAX_CHIPS = 5;

export type SuggestItem = { id: number; naam: string };

export type SearchResponse = {
  hits: Record<string, unknown>[];
  total: number;
  facets?: Record<string, FacetValue[]>;
  timeline?: YearCount[];
  timeline_meta?: TimelineMeta | null;
};

/** Aggregates only (overview / Samenvatting) — no hit rows. */
export type SummaryResponse = Omit<SearchResponse, 'hits'>;

export type FacetValue = { key: string; label: string; count: number };

export type BrowseResponse = {
  hits: Record<string, unknown>[];
  total: number;
  letter: string;
  letters: { letter: string; count: number }[];
};
