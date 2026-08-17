/** Year histogram helpers (D-UI-14d). */

import { PERIOD_KEYS, PERIOD_LABELS } from './facetChart';

export type TimelineBin = 'year' | 'decade';

export type YearCount = {
  year: number;
  count: number;
  by_period?: Record<string, number>;
};

export type TimelineMeta = {
  field: string;
  bin: TimelineBin;
  undated: number;
  stacked?: boolean;
};

/** Chart title for personen birth-year histogram. */
export function birthYearChartTitle(includeShadowDates: boolean): string {
  return includeShadowDates
    ? 'Geboortejaar (incl. schatting)'
    : 'Geboortejaar (alleen expliciet vastgelegd)';
}

export function aanstellingVanChartTitle(): string {
  return 'Startjaar aanstelling';
}

export function timelineChartTitle(
  entity: 'personen' | 'aanstellingen',
  includeShadowDates: boolean
): string {
  if (entity === 'aanstellingen') return aanstellingVanChartTitle();
  return birthYearChartTitle(includeShadowDates);
}

export function timelineStackTotal(bin: YearCount): number {
  if (bin.by_period && Object.keys(bin.by_period).length > 0) {
    return Object.values(bin.by_period).reduce((a, b) => a + b, 0);
  }
  return bin.count;
}

export function stackSegmentFlex(segment: number, stackTotal: number): number {
  if (stackTotal <= 0 || segment <= 0) return 0;
  return segment;
}

export function timelineBarHeight(count: number, max: number): number {
  if (max <= 0 || count <= 0) return 0;
  return Math.round((count / max) * 1000) / 10;
}

export function timelineBinLabel(
  year: number,
  bin: TimelineBin,
  opts?: { shortDecade?: boolean }
): string {
  if (bin === 'decade') {
    return opts?.shortDecade ? String(year) : `${year}–${year + 9}`;
  }
  return String(year);
}

/** How many bin labels to skip between visible ticks (1 = every bar). */
export function timelineLabelStep(binCount: number, maxLabels = 12): number {
  if (binCount <= maxLabels) return 1;
  return Math.ceil(binCount / maxLabels);
}

export function shouldShowTimelineLabel(
  index: number,
  binCount: number,
  maxLabels = 12
): boolean {
  if (binCount <= 1) return true;
  const step = timelineLabelStep(binCount, maxLabels);
  if (step <= 1) return true;
  if (index === 0 || index === binCount - 1) return true;
  return index % step === 0;
}

export function periodShortLabel(key: string): string {
  const full = PERIOD_LABELS[key] ?? key;
  return full.split(' (')[0] ?? full;
}

export function timelineFilterYears(
  year: number,
  bin: TimelineBin
): { from: string; to: string } {
  if (bin === 'decade') {
    return { from: String(year), to: String(year + 9) };
  }
  return { from: String(year), to: String(year) };
}

export function geboorteEdtfRange(from: string, to: string): string {
  return from === to ? `${from}/${from}` : `${from}/${to}`;
}

/** Footnote when hits lack a year on the histogram axis. */
export function undatedTimelineNote(
  undated: number,
  includeShadowDates: boolean
): string | null {
  if (undated <= 0) return null;
  if (includeShadowDates) {
    return `${undated} zonder geboortejaar (ook geen schatting).`;
  }
  return `${undated} zonder expliciet vastgelegd geboortejaar (schattingen niet meegeteld).`;
}

export function aanstellingUndatedNote(undated: number): string | null {
  if (undated <= 0) return null;
  return `${undated} zonder startdatum (van).`;
}

export function undatedNoteForEntity(
  entity: 'personen' | 'aanstellingen',
  undated: number,
  includeShadowDates: boolean
): string | null {
  if (entity === 'aanstellingen') return aanstellingUndatedNote(undated);
  return undatedTimelineNote(undated, includeShadowDates);
}

export function stackedTimelineNote(): string {
  return 'Gestapeld per periode; overlappende personen/aanstellingen tellen in meerdere kleuren.';
}

export { PERIOD_KEYS };
