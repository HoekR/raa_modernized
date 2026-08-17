import { describe, expect, it } from 'vitest';
import { barWidthPct, orderPeriodFacets, topFacetBars } from './facetChart';

describe('barWidthPct', () => {
  it('returns 0 for empty or zero max', () => {
    expect(barWidthPct(10, 0)).toBe(0);
    expect(barWidthPct(0, 100)).toBe(0);
  });

  it('scales count to percentage of max', () => {
    expect(barWidthPct(50, 100)).toBe(50);
    expect(barWidthPct(1, 3)).toBe(33.3);
  });
});

describe('topFacetBars', () => {
  it('slices to maxBars and reports remainder', () => {
    const values = Array.from({ length: 10 }, (_, i) => ({
      key: String(i),
      label: `Item ${i}`,
      count: i,
    }));
    const { shown, rest } = topFacetBars(values, 8);
    expect(shown).toHaveLength(8);
    expect(rest).toBe(2);
  });
});

describe('orderPeriodFacets', () => {
  it('orders periods and fills missing keys with zero counts', () => {
    const ordered = orderPeriodFacets([
      { key: 'republiek', label: 'Republiek (1588–1795)', count: 42 },
      { key: 'me', label: 'Middeleeuwen (1428–1588)', count: 7 },
    ]);
    expect(ordered.map((v) => v.key)).toEqual(['me', 'republiek', 'batfra', 'negentiende_eeuw']);
    expect(ordered[2].count).toBe(0);
    expect(ordered[2].label).toContain('Bataafs');
  });
});
