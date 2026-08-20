import type { SuggestItem } from './period';

export type EntityKind = 'personen' | 'aanstellingen';

export type NameSearchMode = 'prefix' | 'contains' | 'pattern' | 'exact';

export type PersonenNameParts = {
  geslachtsnaam: string;
  voornaam: string;
  tussenvoegsel: string;
  alias: string;
  heerlijkheid: string;
};

export const EMPTY_NAME_PARTS: PersonenNameParts = {
  geslachtsnaam: '',
  voornaam: '',
  tussenvoegsel: '',
  alias: '',
  heerlijkheid: '',
};

export type SharedSearchState = {
  q: string;
  van: string;
  tot: string;
  functieIds: number[];
  instellingIds: number[];
  provincieIds: number[];
  regioIds: number[];
  lokalIds: number[];
  standIds: number[];
  adel: boolean;
  functieMatch: 'any' | 'all';
  instellingMatch: 'any' | 'all';
};

export type PersonenSearchState = SharedSearchState & {
  letter: string | null;
  geboorte: string;
  overlijden: string;
  dateMode: 'incl_shadow' | 'exact';
  qMode: NameSearchMode;
  nameParts: PersonenNameParts;
};

export type AanstellingenSearchState = SharedSearchState & {
  groupBy: 'instelling' | 'functie';
  sort: string;
};

function parseIds(params: URLSearchParams, key: string): number[] {
  const raw = params.get(key);
  if (!raw) return [];
  return raw
    .split(',')
    .map((part) => Number(part.trim()))
    .filter((n) => !Number.isNaN(n));
}

function setIds(params: URLSearchParams, key: string, ids: number[]) {
  if (ids.length) params.set(key, ids.join(','));
}

function parseShared(params: URLSearchParams): SharedSearchState {
  return {
    q: params.get('q') ?? '',
    van: params.get('van') ?? '',
    tot: params.get('tot') ?? '',
    functieIds: parseIds(params, 'functie_id'),
    instellingIds: parseIds(params, 'instelling_id'),
    provincieIds: parseIds(params, 'provincie_id'),
    regioIds: parseIds(params, 'regio_id'),
    lokalIds: parseIds(params, 'lokaal_id'),
    standIds: parseIds(params, 'stand_id'),
    adel: params.get('adel') === '1',
    functieMatch: params.get('functie_match') === 'all' ? 'all' : 'any',
    instellingMatch: params.get('instelling_match') === 'all' ? 'all' : 'any',
  };
}

function writeShared(params: URLSearchParams, state: SharedSearchState) {
  if (state.q.trim()) params.set('q', state.q.trim());
  if (state.van.trim()) params.set('van', state.van.trim());
  if (state.tot.trim()) params.set('tot', state.tot.trim());
  setIds(params, 'functie_id', state.functieIds);
  setIds(params, 'instelling_id', state.instellingIds);
  setIds(params, 'provincie_id', state.provincieIds);
  setIds(params, 'regio_id', state.regioIds);
  setIds(params, 'lokaal_id', state.lokalIds);
  setIds(params, 'stand_id', state.standIds);
  if (state.adel) params.set('adel', '1');
  if (state.functieMatch === 'all') params.set('functie_match', 'all');
  if (state.instellingMatch === 'all') params.set('instelling_match', 'all');
}

export function parsePersonenParams(params: URLSearchParams): PersonenSearchState {
  const shared = parseShared(params);
  const letter = params.get('letter');
  const qModeRaw = params.get('q_mode');
  const qMode: NameSearchMode =
    qModeRaw === 'contains' || qModeRaw === 'pattern' || qModeRaw === 'exact'
      ? qModeRaw
      : 'prefix';
  return {
    ...shared,
    letter: letter && letter.length === 1 ? letter : null,
    geboorte: params.get('geboorte') ?? '',
    overlijden: params.get('overlijden') ?? '',
    dateMode: params.get('date_mode') === 'exact' ? 'exact' : 'incl_shadow',
    qMode,
    nameParts: {
      geslachtsnaam: params.get('geslachtsnaam') ?? '',
      voornaam: params.get('voornaam') ?? '',
      tussenvoegsel: params.get('tussenvoegsel') ?? '',
      alias: params.get('alias') ?? '',
      heerlijkheid: params.get('heerlijkheid') ?? '',
    },
  };
}

export function parseAanstellingenParams(params: URLSearchParams): AanstellingenSearchState {
  const shared = parseShared(params);
  const groupBy = params.get('group_by');
  return {
    ...shared,
    groupBy: groupBy === 'functie' ? 'functie' : 'instelling',
    sort: params.get('sort') ?? 'van',
  };
}

export function buildPersonenParams(state: PersonenSearchState, period: string): URLSearchParams {
  const params = new URLSearchParams();
  writeShared(params, state);
  if (state.letter) params.set('letter', state.letter);
  if (state.geboorte.trim()) params.set('geboorte', state.geboorte.trim());
  if (state.overlijden.trim()) params.set('overlijden', state.overlijden.trim());
  if (state.dateMode === 'exact') params.set('date_mode', 'exact');
  if (state.qMode !== 'prefix') params.set('q_mode', state.qMode);
  for (const [key, value] of Object.entries(state.nameParts)) {
    if (value.trim()) params.set(key, value.trim());
  }
  if (period) params.set('period', period);
  return params;
}

export function buildAanstellingenParams(
  state: AanstellingenSearchState,
  period: string
): URLSearchParams {
  const params = new URLSearchParams();
  writeShared(params, state);
  if (state.groupBy !== 'instelling') params.set('group_by', state.groupBy);
  if (state.sort && state.sort !== 'van') params.set('sort', state.sort);
  if (period) params.set('period', period);
  return params;
}

export function sharedFilters(state: SharedSearchState): Record<string, string[]> {
  const filters: Record<string, string[]> = {};
  if (state.functieIds.length) filters.functie_id = state.functieIds.map(String);
  if (state.instellingIds.length) filters.instelling_id = state.instellingIds.map(String);
  if (state.provincieIds.length) filters.provincie_id = state.provincieIds.map(String);
  if (state.regioIds.length) filters.regio_id = state.regioIds.map(String);
  if (state.lokalIds.length) filters.lokaal_id = state.lokalIds.map(String);
  if (state.standIds.length) filters.stand_id = state.standIds.map(String);
  if (state.adel) filters.adel = ['1'];
  if (state.van.trim()) filters.van = [state.van.trim()];
  if (state.tot.trim()) filters.tot = [state.tot.trim()];
  return filters;
}

export function personenFilters(state: PersonenSearchState): Record<string, string[]> {
  const filters = sharedFilters(state);
  if (state.geboorte.trim()) filters.geboorte = [state.geboorte.trim()];
  if (state.overlijden.trim()) filters.overlijden = [state.overlijden.trim()];
  if (state.letter) filters.letter = [state.letter];
  for (const [key, value] of Object.entries(state.nameParts)) {
    if (value.trim()) filters[key] = [value.trim()];
  }
  return filters;
}

const NAME_PART_LABELS: Record<keyof PersonenNameParts, string> = {
  geslachtsnaam: 'Geslachtsnaam',
  voornaam: 'Voornaam',
  tussenvoegsel: 'Tussenvoegsel',
  alias: 'Naamsvariant',
  heerlijkheid: 'Heerlijkheid',
};

export function namePartChipLabel(key: keyof PersonenNameParts, value: string): string {
  return `${NAME_PART_LABELS[key]}: ${value.trim()}`;
}

export function hasNameParts(parts: PersonenNameParts): boolean {
  return Object.values(parts).some((v) => v.trim());
}

export function overviewHref(
  entity: EntityKind,
  state: PersonenSearchState | AanstellingenSearchState,
  period: string
): string {
  const params =
    entity === 'personen'
      ? buildPersonenParams(state as PersonenSearchState, period)
      : buildAanstellingenParams(state as AanstellingenSearchState, period);
  const qs = params.toString();
  return `/${entity}/overzicht${qs ? `?${qs}` : ''}`;
}

export function listHref(
  entity: EntityKind,
  state: PersonenSearchState | AanstellingenSearchState,
  period: string
): string {
  const params =
    entity === 'personen'
      ? buildPersonenParams(state as PersonenSearchState, period)
      : buildAanstellingenParams(state as AanstellingenSearchState, period);
  const qs = params.toString();
  return `/${entity}${qs ? `?${qs}` : ''}`;
}

/** List route path for personen (URL sync after filter changes). */
export function personenListPath(state: PersonenSearchState, period: string): string {
  return listHref('personen', state, period);
}

export function applyPeriodFromParams(params: URLSearchParams): string | null {
  const period = params.get('period');
  if (!period) return null;
  return period;
}

export async function resolveSuggestItems(
  fetcher: (id: number) => Promise<{ id: number; naam: string }>,
  ids: number[]
): Promise<SuggestItem[]> {
  if (!ids.length) return [];
  return Promise.all(
    ids.map(async (id) => {
      try {
        const row = await fetcher(id);
        return { id: row.id, naam: row.naam };
      } catch {
        return { id, naam: `#${id}` };
      }
    })
  );
}

export function toggleId(list: number[], id: number): number[] {
  return list.includes(id) ? list.filter((x) => x !== id) : [...list, id];
}

/** Chip label for EDTF slash range (e.g. geboorte/overlijden filters). */
export function edtfRangeChipLabel(prefix: string, value: string): string {
  const v = value.trim();
  if (!v) return '';
  const parts = v.split('/').map((s) => s.trim());
  if (parts.length === 2 && parts[0] && parts[1]) {
    const [from, to] = parts;
    if (from === to) return `${prefix}: ${from}`;
    return `${prefix}: ${from}–${to}`;
  }
  return `${prefix}: ${v}`;
}

/** Chip label for aanstelling van/tot year filters. */
export function aanstellingDateChipLabel(van: string, tot: string): string | null {
  const v = van.trim();
  const t = tot.trim();
  if (!v && !t) return null;
  if (v && t && v !== t) return `Aanstelling: ${v}–${t}`;
  if (v && t) return `Aanstelling: ${v}`;
  if (v) return `Aanstelling vanaf ${v}`;
  return `Aanstelling t/m ${t}`;
}
