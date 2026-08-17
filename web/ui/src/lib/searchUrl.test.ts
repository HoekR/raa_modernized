import { describe, expect, it } from 'vitest';
import {
  EMPTY_NAME_PARTS,
  aanstellingDateChipLabel,
  buildAanstellingenParams,
  buildPersonenParams,
  edtfRangeChipLabel,
  parseAanstellingenParams,
  parsePersonenParams,
  personenFilters,
} from './searchUrl';

describe('searchUrl personen roundtrip', () => {
  it('encodes and parses filters', () => {
    const state = {
      q: 'aylva',
      van: '1750',
      tot: '',
      functieIds: [561, 1038],
      instellingIds: [171],
      provincieIds: [],
      regioIds: [],
      lokalIds: [],
      standIds: [2],
      adel: true,
      functieMatch: 'all' as const,
      instellingMatch: 'any' as const,
      letter: null,
      geboorte: '1700/1750',
      overlijden: '',
      dateMode: 'exact' as const,
      qMode: 'prefix' as const,
      nameParts: { ...EMPTY_NAME_PARTS },
    };
    const params = buildPersonenParams(state, 'republiek');
    const parsed = parsePersonenParams(params);
    expect(parsed.q).toBe('aylva');
    expect(parsed.functieIds).toEqual([561, 1038]);
    expect(parsed.instellingIds).toEqual([171]);
    expect(parsed.adel).toBe(true);
    expect(parsed.geboorte).toBe('1700/1750');
    expect(parsed.dateMode).toBe('exact');
    expect(params.get('period')).toBe('republiek');
  });

  it('builds API filters', () => {
    const filters = personenFilters({
      q: '',
      qMode: 'prefix',
      nameParts: { ...EMPTY_NAME_PARTS },
      van: '1750',
      tot: '1770',
      functieIds: [561],
      instellingIds: [],
      provincieIds: [],
      regioIds: [],
      lokalIds: [],
      standIds: [],
      adel: false,
      functieMatch: 'any',
      instellingMatch: 'any',
      letter: 'A',
      geboorte: '',
      overlijden: '',
      dateMode: 'incl_shadow',
    });
    expect(filters.functie_id).toEqual(['561']);
    expect(filters.letter).toEqual(['A']);
    expect(filters.van).toEqual(['1750']);
    expect(filters.tot).toEqual(['1770']);
  });
});

describe('filter chip labels', () => {
  it('formats single-year geboorte', () => {
    expect(edtfRangeChipLabel('Geboorte', '1750/1750')).toBe('Geboorte: 1750');
  });

  it('formats decade geboorte', () => {
    expect(edtfRangeChipLabel('Geboorte', '1750/1759')).toBe('Geboorte: 1750–1759');
  });

  it('formats aanstelling range', () => {
    expect(aanstellingDateChipLabel('1750', '1759')).toBe('Aanstelling: 1750–1759');
  });
});

describe('searchUrl aanstellingen roundtrip', () => {
  it('encodes group and sort', () => {
    const state = {
      q: '',
      van: '',
      tot: '',
      functieIds: [1316],
      instellingIds: [],
      provincieIds: [],
      regioIds: [],
      lokalIds: [],
      standIds: [],
      adel: false,
      functieMatch: 'any' as const,
      instellingMatch: 'any' as const,
      groupBy: 'functie' as const,
      sort: 'van',
    };
    const parsed = parseAanstellingenParams(buildAanstellingenParams(state, 'all'));
    expect(parsed.functieIds).toEqual([1316]);
    expect(parsed.groupBy).toBe('functie');
    expect(parsed.sort).toBe('van');
  });
});
