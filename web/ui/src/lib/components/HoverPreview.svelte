<script lang="ts">
  import type { Snippet } from 'svelte';
  import { clampPreviewTop } from '$lib/hoverPreview';

  let {
    open = false,
    anchorTop = 0,
    title = '',
    href,
    children,
    onenter,
    onleave,
  }: {
    open?: boolean;
    anchorTop?: number;
    title?: string;
    href?: string;
    children?: Snippet;
    onenter?: () => void;
    onleave?: () => void;
  } = $props();

  let cardEl = $state<HTMLElement | null>(null);
  let cardHeight = $state(280);

  const top = $derived(
    typeof window === 'undefined'
      ? Math.max(8, anchorTop)
      : clampPreviewTop(anchorTop, cardHeight, window.innerHeight)
  );

  $effect(() => {
    if (!open || !cardEl) return;
    const el = cardEl;
    const update = () => {
      cardHeight = el.getBoundingClientRect().height;
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  });
</script>

{#if open}
  <aside
    bind:this={cardEl}
    class="hover-preview"
    style="top: {top}px"
    aria-label={title || 'Voorvertoning'}
    onmouseenter={onenter}
    onmouseleave={onleave}
  >
    <div class="hover-preview-head">
      <h2>{title || 'Voorvertoning'}</h2>
      {#if href}
        <a href={href} onclick={(e) => e.stopPropagation()}>Volledige pagina →</a>
      {/if}
    </div>
    <div class="hover-preview-body">
      {@render children?.()}
    </div>
  </aside>
{/if}
