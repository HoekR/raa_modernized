import type { FacetValue } from './period';

export const PERIOD_KEYS = ['me', 'republiek', 'batfra', 'negentiende_eeuw'] as const;

export const PERIOD_LABELS: Record<string, string> = {
  me: 'Middeleeuwen (1428–1588)',
  republiek: 'Republiek (1588–1795)',
  batfra: 'Bataafs-Franse tijd (1795–1813)',
  negentiende_eeuw: 'Negentiende eeuw (1813–1861)',
};

export const PERIOD_COLOR_VAR: Record<string, string> = {
  me: 'var(--raa-period-me)',
  republiek: 'var(--raa-period-republiek)',
  batfra: 'var(--raa-period-batfra)',
  negentiende_eeuw: 'var(--raa-period-negentiende)',
};

export function barWidthPct(count: number, max: number): number {
  if (max <= 0 || count <= 0) return 0;
  return Math.round((count / max) * 1000) / 10;
}

export function topFacetBars(
  values: FacetValue[],
  maxBars = 8
): { shown: FacetValue[]; rest: number } {
  const shown = values.slice(0, maxBars);
  return { shown, rest: Math.max(0, values.length - maxBars) };
}

/** Fixed period order; missing keys get count 0 and fallback label. */
export function orderPeriodFacets(values: FacetValue[]): FacetValue[] {
  const byKey = new Map(values.map((v) => [v.key, v]));
  return PERIOD_KEYS.map(
    (key) => byKey.get(key) ?? { key, label: PERIOD_LABELS[key] ?? key, count: 0 }
  );
}

export function periodBarColor(key: string): string {
  return PERIOD_COLOR_VAR[key] ?? 'var(--raa-accent)';
}
