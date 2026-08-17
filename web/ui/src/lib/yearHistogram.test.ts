import { describe, expect, it } from 'vitest';
import {
  birthYearChartTitle,
  geboorteEdtfRange,
  stackSegmentFlex,
  timelineBarHeight,
  timelineBinLabel,
  shouldShowTimelineLabel,
  timelineFilterYears,
  timelineStackTotal,
  undatedTimelineNote,
} from './yearHistogram';

describe('birthYearChartTitle', () => {
  it('labels shadow-inclusive mode', () => {
    expect(birthYearChartTitle(true)).toBe('Geboortejaar (incl. schatting)');
  });

  it('labels exact mode', () => {
    expect(birthYearChartTitle(false)).toBe('Geboortejaar (alleen expliciet vastgelegd)');
  });
});

describe('timelineStackTotal', () => {
  it('sums stacked segments', () => {
    expect(
      timelineStackTotal({
        year: 1750,
        count: 5,
        by_period: { me: 1, republiek: 4 },
      })
    ).toBe(5);
  });
});

describe('timelineBarHeight', () => {
  it('scales to percentage of max', () => {
    expect(timelineBarHeight(50, 100)).toBe(50);
  });
});

describe('timelineBinLabel', () => {
  it('formats decades', () => {
    expect(timelineBinLabel(1750, 'decade')).toBe('1750–1759');
  });

  it('shortens dense decade labels', () => {
    expect(timelineBinLabel(1750, 'decade', { shortDecade: true })).toBe('1750');
  });
});

describe('shouldShowTimelineLabel', () => {
  it('shows all labels when few bins', () => {
    expect(shouldShowTimelineLabel(0, 8, 12)).toBe(true);
    expect(shouldShowTimelineLabel(7, 8, 12)).toBe(true);
  });

  it('thins labels for long timelines', () => {
    const visible = Array.from({ length: 44 }, (_, i) =>
      shouldShowTimelineLabel(i, 44, 12)
    ).filter(Boolean).length;
    expect(visible).toBeLessThanOrEqual(15);
    expect(visible).toBeGreaterThanOrEqual(10);
  });
});

describe('timelineFilterYears', () => {
  it('returns a single year', () => {
    expect(timelineFilterYears(1750, 'year')).toEqual({ from: '1750', to: '1750' });
  });
});

describe('geboorteEdtfRange', () => {
  it('uses slash form for one year', () => {
    expect(geboorteEdtfRange('1750', '1750')).toBe('1750/1750');
  });
});

describe('stackSegmentFlex', () => {
  it('returns segment count as flex weight', () => {
    expect(stackSegmentFlex(4, 10)).toBe(4);
  });
});

describe('undatedTimelineNote', () => {
  it('explains undated in exact mode', () => {
    expect(undatedTimelineNote(12, false)).toContain('niet meegeteld');
  });
});
