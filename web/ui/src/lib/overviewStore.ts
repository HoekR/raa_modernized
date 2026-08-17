import type { FacetValue } from './period';
import type { TimelineMeta, YearCount } from './yearHistogram';
import type { AanstellingenSearchState, EntityKind, PersonenSearchState } from './searchUrl';

export type OverviewSnapshot = {
  entity: EntityKind;
  period: string;
  personen?: PersonenSearchState;
  aanstellingen?: AanstellingenSearchState;
  total: number;
  facets: Record<string, FacetValue[]>;
  timeline: YearCount[];
  timelineMeta: TimelineMeta | null;
};

const STORAGE_KEY = 'raa-overview-snapshot';

export function saveOverviewSnapshot(snapshot: OverviewSnapshot): void {
  if (typeof sessionStorage === 'undefined') return;
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot));
  } catch {
    /* quota / private mode */
  }
}

export function loadOverviewSnapshot(entity: EntityKind): OverviewSnapshot | null {
  if (typeof sessionStorage === 'undefined') return null;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as OverviewSnapshot;
    return data.entity === entity ? data : null;
  } catch {
    return null;
  }
}

export function updateOverviewSnapshot(patch: Partial<OverviewSnapshot>): void {
  if (typeof sessionStorage === 'undefined') return;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const data = { ...JSON.parse(raw), ...patch } as OverviewSnapshot;
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch {
    /* ignore */
  }
}

export function patchOverviewPersonen(state: PersonenSearchState, period: string): void {
  updateOverviewSnapshot({ entity: 'personen', period, personen: state });
}
