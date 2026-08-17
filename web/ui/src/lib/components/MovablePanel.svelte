<script lang="ts">
  import type { Snippet } from 'svelte';
  import { tick } from 'svelte';
  import {
    clampPanelPosition,
    defaultPanelPosition,
    loadPanelPosition,
    savePanelPosition,
    type PanelPosition,
  } from '$lib/draggablePanel';

  let {
    open = $bindable(false),
    title = '',
    storageKey = 'raa-movable-panel',
    children,
  }: {
    open?: boolean;
    title?: string;
    storageKey?: string;
    children?: Snippet;
  } = $props();

  let panelEl = $state<HTMLElement | null>(null);
  let pos = $state<PanelPosition>({ x: 16, y: 96 });
  let dragging = $state(false);
  let dragOffset = { x: 0, y: 0 };

  function clampToViewport(next: PanelPosition): PanelPosition {
    if (typeof window === 'undefined' || !panelEl) return next;
    const rect = panelEl.getBoundingClientRect();
    return clampPanelPosition(next, rect.width, rect.height, window.innerWidth, window.innerHeight);
  }

  function initPosition() {
    if (typeof window === 'undefined') return;
    const width = panelEl?.getBoundingClientRect().width ?? 280;
    const fallback = defaultPanelPosition(window.innerWidth, window.innerHeight, width);
    pos = clampToViewport(loadPanelPosition(storageKey, fallback));
  }

  function onResize() {
    if (!open) return;
    pos = clampToViewport(pos);
  }

  function onPointerMove(e: PointerEvent) {
    if (!dragging) return;
    pos = clampToViewport({ x: e.clientX - dragOffset.x, y: e.clientY - dragOffset.y });
  }

  function endDrag() {
    if (!dragging) return;
    dragging = false;
    savePanelPosition(storageKey, pos);
    window.removeEventListener('pointermove', onPointerMove);
    window.removeEventListener('pointerup', endDrag);
  }

  function onPointerDown(e: PointerEvent) {
    if (e.button !== 0) return;
    dragging = true;
    dragOffset = { x: e.clientX - pos.x, y: e.clientY - pos.y };
    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', endDrag);
  }

  function close() {
    open = false;
  }

  $effect(() => {
    if (!open) return;
    void (async () => {
      await tick();
      initPosition();
    })();
  });

  $effect(() => {
    return () => {
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', endDrag);
    };
  });
</script>

<svelte:window onresize={onResize} />

{#if open}
  <aside
    bind:this={panelEl}
    class="movable-panel"
    class:dragging
    style="left: {pos.x}px; top: {pos.y}px"
    aria-labelledby="movable-panel-title"
  >
    <div class="panel-head">
      <button
        type="button"
        class="panel-drag"
        aria-label="Paneel slepen"
        onpointerdown={onPointerDown}
      >
        ⋮⋮
      </button>
      <h2 id="movable-panel-title">{title}</h2>
      <button type="button" class="panel-close" aria-label="Sluiten" onclick={close}>×</button>
    </div>
    <div class="panel-body">
      {@render children?.()}
    </div>
  </aside>
{/if}

<style>
  .movable-panel {
    position: fixed;
    z-index: 180;
    width: min(22rem, calc(100vw - 2rem));
    max-height: min(70vh, 34rem);
    display: flex;
    flex-direction: column;
    background: var(--raa-surface);
    border: 1px solid var(--raa-line-strong);
    border-radius: var(--raa-radius);
    box-shadow: var(--raa-shadow);
    overflow: hidden;
  }
  .movable-panel.dragging {
    user-select: none;
    cursor: grabbing;
  }
  .panel-head {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 0.35rem;
    padding: 0.55rem 0.65rem;
    border-bottom: 2px solid var(--raa-accent-bright);
    flex-shrink: 0;
  }
  .panel-drag {
    border: 0;
    background: transparent;
    color: var(--raa-ink-faint);
    cursor: grab;
    padding: 0.1rem 0.2rem;
    font-size: 0.85rem;
    line-height: 1;
    touch-action: none;
  }
  .movable-panel.dragging .panel-drag {
    cursor: grabbing;
  }
  .panel-drag:hover,
  .panel-drag:focus-visible {
    color: var(--raa-accent);
    outline: none;
  }
  h2 {
    margin: 0;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--raa-accent);
  }
  .panel-close {
    border: 0;
    background: transparent;
    font-size: 1.25rem;
    line-height: 1;
    cursor: pointer;
    color: var(--raa-ink-muted);
    padding: 0 0.1rem;
  }
  .panel-close:hover {
    color: var(--raa-ink);
  }
  .panel-body {
    overflow: auto;
    padding: 0.85rem 0.75rem;
  }
</style>
