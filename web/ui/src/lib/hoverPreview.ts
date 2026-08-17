/** Hover-preview helpers for search result rows (Goetgevonden-style peek). */

export function prefersHoverPreview(): boolean {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return false;
  }
  return window.matchMedia('(hover: hover) and (pointer: fine)').matches;
}

export function clampPreviewTop(anchorTop: number, cardHeight: number, viewportHeight: number, margin = 8): number {
  if (anchorTop + cardHeight <= viewportHeight - margin) {
    return Math.max(margin, anchorTop);
  }
  return Math.max(margin, viewportHeight - cardHeight - margin);
}

export class HoverPreviewController {
  showDelay: number;
  hideDelay: number;
  visible = false;
  private showTimer: ReturnType<typeof setTimeout> | null = null;
  private hideTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(opts?: { showDelay?: number; hideDelay?: number }) {
    this.showDelay = opts?.showDelay ?? 280;
    this.hideDelay = opts?.hideDelay ?? 160;
  }

  scheduleShow(fn: () => void, { alreadyVisible = false } = {}) {
    this.clearHide();
    this.clearShow();
    if (alreadyVisible || this.visible) {
      this.visible = true;
      fn();
      return;
    }
    this.showTimer = setTimeout(() => {
      this.showTimer = null;
      this.visible = true;
      fn();
    }, this.showDelay);
  }

  scheduleHide(fn: () => void) {
    this.clearShow();
    this.clearHide();
    this.hideTimer = setTimeout(() => {
      this.hideTimer = null;
      this.visible = false;
      fn();
    }, this.hideDelay);
  }

  cancel() {
    this.clearShow();
    this.clearHide();
  }

  hideNow(fn: () => void) {
    this.cancel();
    this.visible = false;
    fn();
  }

  private clearShow() {
    if (this.showTimer != null) {
      clearTimeout(this.showTimer);
      this.showTimer = null;
    }
  }

  private clearHide() {
    if (this.hideTimer != null) {
      clearTimeout(this.hideTimer);
      this.hideTimer = null;
    }
  }
}

export function previewAnchor(el: EventTarget | null): HTMLElement | null {
  if (!(el instanceof HTMLElement)) return null;
  return el.closest('tr') ?? el;
}

/** Shared hover-preview handlers for personen/aanstellingen search rows. */
export function createPersoonPreviewHandlers(opts: {
  hoverCtl: HoverPreviewController;
  isBlocked: () => boolean;
  getActiveId: () => number | null;
  show: (id: number, top: number) => void;
  hide: () => void;
}) {
  const { hoverCtl, isBlocked, getActiveId, show, hide } = opts;

  function hideNow() {
    hoverCtl.hideNow(hide);
  }

  function showPreview(e: MouseEvent | FocusEvent, id: number) {
    if (isBlocked()) return;
    const row = previewAnchor(e.currentTarget);
    if (!row) return;
    hoverCtl.scheduleShow(() => {
      show(id, row.getBoundingClientRect().top);
    }, { alreadyVisible: getActiveId() === id });
  }

  function hidePreviewSoon() {
    hoverCtl.scheduleHide(hide);
  }

  function togglePreview(e: MouseEvent, id: number) {
    if (prefersHoverPreview()) return;
    e.preventDefault();
    if (getActiveId() === id) {
      hideNow();
      return;
    }
    const row = previewAnchor(e.currentTarget);
    if (!row) return;
    hoverCtl.hideNow(() => {});
    show(id, row.getBoundingClientRect().top);
    hoverCtl.visible = true;
  }

  return { hideNow, showPreview, hidePreviewSoon, togglePreview };
}
