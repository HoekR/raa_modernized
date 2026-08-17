export type PanelPosition = { x: number; y: number };

export function clampPanelPosition(
  pos: PanelPosition,
  panelW: number,
  panelH: number,
  viewportW: number,
  viewportH: number,
  margin = 8
): PanelPosition {
  const maxX = Math.max(margin, viewportW - panelW - margin);
  const maxY = Math.max(margin, viewportH - panelH - margin);
  return {
    x: Math.min(Math.max(margin, pos.x), maxX),
    y: Math.min(Math.max(margin, pos.y), maxY),
  };
}

export function defaultPanelPosition(
  viewportW: number,
  _viewportH: number,
  panelW: number
): PanelPosition {
  return {
    x: Math.max(8, viewportW - panelW - 16),
    y: 96,
  };
}

export function loadPanelPosition(storageKey: string, fallback: PanelPosition): PanelPosition {
  if (typeof sessionStorage === 'undefined') return fallback;
  try {
    const raw = sessionStorage.getItem(storageKey);
    if (!raw) return fallback;
    const parsed = JSON.parse(raw) as PanelPosition;
    if (typeof parsed.x === 'number' && typeof parsed.y === 'number') return parsed;
  } catch {
    /* ignore corrupt storage */
  }
  return fallback;
}

export function savePanelPosition(storageKey: string, pos: PanelPosition): void {
  if (typeof sessionStorage === 'undefined') return;
  try {
    sessionStorage.setItem(storageKey, JSON.stringify(pos));
  } catch {
    /* ignore quota errors */
  }
}
