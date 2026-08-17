import { describe, expect, it } from 'vitest';
import { clampPanelPosition, defaultPanelPosition } from './draggablePanel';

describe('clampPanelPosition', () => {
  it('keeps the panel inside the viewport', () => {
    expect(clampPanelPosition({ x: 500, y: 900 }, 240, 320, 800, 600)).toEqual({
      x: 500,
      y: 272,
    });
  });

  it('applies a minimum margin', () => {
    expect(clampPanelPosition({ x: -20, y: -10 }, 240, 320, 800, 600)).toEqual({
      x: 8,
      y: 8,
    });
  });
});

describe('defaultPanelPosition', () => {
  it('anchors near the right edge', () => {
    expect(defaultPanelPosition(1000, 800, 280)).toEqual({ x: 704, y: 96 });
  });
});
