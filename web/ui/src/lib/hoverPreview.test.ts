import { afterEach, describe, expect, it, vi } from 'vitest';
import { clampPreviewTop, HoverPreviewController } from './hoverPreview';

describe('clampPreviewTop', () => {
  it('keeps the card aligned with the row when it fits', () => {
    expect(clampPreviewTop(120, 200, 800)).toBe(120);
  });

  it('shifts up when the card would overflow the viewport', () => {
    expect(clampPreviewTop(700, 200, 800)).toBe(592);
  });
});

describe('HoverPreviewController', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('delays the first show', () => {
    vi.useFakeTimers();
    const ctl = new HoverPreviewController({ showDelay: 280, hideDelay: 160 });
    const shown: number[] = [];
    ctl.scheduleShow(() => shown.push(1));
    vi.advanceTimersByTime(279);
    expect(shown).toEqual([]);
    vi.advanceTimersByTime(1);
    expect(shown).toEqual([1]);
    expect(ctl.visible).toBe(true);
  });

  it('switches immediately while already visible', () => {
    vi.useFakeTimers();
    const ctl = new HoverPreviewController({ showDelay: 280, hideDelay: 160 });
    const shown: number[] = [];
    ctl.scheduleShow(() => shown.push(1));
    vi.advanceTimersByTime(280);
    ctl.scheduleShow(() => shown.push(2));
    expect(shown).toEqual([1, 2]);
  });

  it('cancels hide when entering another row', () => {
    vi.useFakeTimers();
    const ctl = new HoverPreviewController({ showDelay: 280, hideDelay: 160 });
    let id: number | null = 1;
    ctl.visible = true;
    ctl.scheduleHide(() => {
      id = null;
    });
    ctl.scheduleShow(() => {
      id = 2;
    });
    vi.advanceTimersByTime(160);
    expect(id).toBe(2);
    expect(ctl.visible).toBe(true);
  });
});
