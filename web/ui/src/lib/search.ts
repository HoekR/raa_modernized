import { get } from 'svelte/store';
import { apiGet, apiPost } from './api';
import { periodKey, periodMode, periodParam, type PeriodCount, type SuggestItem } from './period';
import type { BrowseResponse, SearchResponse, SummaryResponse } from './period';

export function periodBodyFields() {
  return {
    period: get(periodParam),
    period_mode: get(periodMode),
  };
}

export async function loadPeriods(context: string): Promise<PeriodCount[]> {
  return apiGet<PeriodCount[]>(`/api/periods?context=${encodeURIComponent(context)}`);
}

export async function suggestField(field: string, q: string): Promise<SuggestItem[]> {
  const params = new URLSearchParams({
    q,
    period: get(periodParam) || '',
    period_mode: get(periodMode),
  });
  return apiGet<SuggestItem[]>(`/api/suggest/${field}?${params}`);
}

export async function searchEntity(
  entity: 'personen' | 'aanstellingen' | 'instellingen' | 'functies',
  body: Record<string, unknown>
): Promise<SearchResponse> {
  return apiPost<SearchResponse>(`/api/search/${entity}`, {
    ...periodBodyFields(),
    ...body,
  });
}

export async function searchSummary(
  entity: 'personen' | 'aanstellingen',
  body: Record<string, unknown>
): Promise<SummaryResponse> {
  return apiPost<SummaryResponse>(`/api/search/${entity}/summary`, {
    ...periodBodyFields(),
    ...body,
  });
}

export async function browseAz(
  entity: 'personen' | 'instellingen' | 'functies',
  opts: { letter?: string | null; from?: number; size?: number }
): Promise<BrowseResponse> {
  const params = new URLSearchParams({
    from: String(opts.from ?? 0),
    size: String(opts.size ?? 100),
    period_mode: get(periodMode),
  });
  const period = get(periodParam);
  if (period) params.set('period', period);
  if (opts.letter) params.set('letter', opts.letter);
  else params.set('letter', 'ALL');
  return apiGet<BrowseResponse>(`/api/browse/${entity}/az?${params}`);
}

export async function loadStands(): Promise<{ id: number; naam: string }[]> {
  return apiGet('/api/stands');
}

export function listingName(row: Record<string, unknown>): string {
  if (row.listing_naam) return String(row.listing_naam);
  if (row.display_naam) return String(row.display_naam);
  const gs = String(row.geslachtsnaam ?? '').trim();
  const vn = String(row.voornaam ?? '').trim();
  const tv = String(row.tussenvoegsel ?? '').trim();
  if (gs) return [gs + ',', vn, tv].filter(Boolean).join(' ').replace(/,\s*$/, '');
  return vn || [vn, tv, gs].filter(Boolean).join(' ');
}

export function personName(row: Record<string, unknown>): string {
  if (row.display_naam) return String(row.display_naam);
  return [row.voornaam, row.tussenvoegsel, row.geslachtsnaam].filter(Boolean).join(' ');
}

const LIFE_YEAR_MIN = 1400;
const LIFE_YEAR_MAX = 1920;

function parseLeadingYear(text: string): number | null {
  const match = text.match(/^(\d{1,4})/);
  return match ? Number(match[1]) : null;
}

function isPlausibleLifeYear(year: number | null): boolean {
  return year != null && year >= LIFE_YEAR_MIN && year <= LIFE_YEAR_MAX;
}

export function lifeCell(
  row: Record<string, unknown>,
  kind: 'geboorte' | 'overlijden'
): { text: string; estimated: boolean; uncertain: boolean } {
  const display = kind === 'geboorte' ? row.geboortedatum_als_bekend : row.overlijdensdatum_als_bekend;
  const edtf = kind === 'geboorte' ? row.geboorte_edtf : row.overlijden_edtf;
  const lifeYear = kind === 'geboorte' ? row.life_start_year : row.life_end_year;
  const lifeSource = kind === 'geboorte' ? row.life_start_source : row.life_end_source;
  const lifeEdtf = kind === 'geboorte' ? row.life_start_edtf : row.life_end_edtf;
  let text = display != null ? String(display).trim() : '';
  const edtfStr = edtf != null ? String(edtf).trim() : '';
  let uncertain = /[~?%]$/.test(edtfStr) || /[~?%]$/.test(text);
  if (text.endsWith('~') || text.endsWith('?') || text.endsWith('%')) {
    text = text.slice(0, -1);
  }
  const leadingYear = text ? parseLeadingYear(text) : null;
  if (text && leadingYear != null && !isPlausibleLifeYear(leadingYear)) {
    text = '';
  }
  if (!text) {
    if (lifeSource === 'shadow' && lifeYear != null && lifeYear !== '') {
      if (kind === 'overlijden' && typeof lifeEdtf === 'string' && lifeEdtf.startsWith('>')) {
        return { text: lifeEdtf, estimated: true, uncertain: false };
      }
      return { text: String(lifeYear), estimated: true, uncertain: false };
    }
    return { text: '—', estimated: false, uncertain: false };
  }
  if (uncertain && !text.toLowerCase().startsWith('ca.')) {
    text = `ca. ${text}`;
  }
  return { text, estimated: false, uncertain };
}

export type NestedGroup = {
  id: unknown;
  naam: string;
  inner: { id: unknown; naam: string; rows: Record<string, unknown>[] }[];
};

export function groupNested(
  hits: Record<string, unknown>[],
  outerKey: string,
  innerKey: string
): NestedGroup[] {
  const groups: NestedGroup[] = [];
  const outerMap = new Map<unknown, NestedGroup & { innerMap: Map<unknown, NestedGroup['inner'][0]> }>();
  for (const row of hits) {
    const outerId = row[`${outerKey}_id`];
    const innerId = row[`${innerKey}_id`];
    let outer = outerMap.get(outerId);
    if (!outer) {
      outer = {
        id: outerId,
        naam: String(row[outerKey] ?? ''),
        inner: [],
        innerMap: new Map(),
      };
      outerMap.set(outerId, outer);
      groups.push(outer);
    }
    let inner = outer.innerMap.get(innerId);
    if (!inner) {
      inner = { id: innerId, naam: String(row[innerKey] ?? ''), rows: [] };
      outer.innerMap.set(innerId, inner);
      outer.inner.push(inner);
    }
    inner.rows.push(row);
  }
  return groups;
}
