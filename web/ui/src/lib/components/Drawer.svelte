<script lang="ts">
  import type { Snippet } from 'svelte';

  let {
    open = $bindable(false),
    title = '',
    wide = false,
    children,
    footer,
  }: {
    open?: boolean;
    title?: string;
    wide?: boolean;
    children?: Snippet;
    footer?: Snippet;
  } = $props();

  function close() {
    open = false;
  }

  function onKey(e: KeyboardEvent) {
    if (e.key === 'Escape' && open) close();
  }
</script>

<svelte:window onkeydown={onKey} />

{#if open}
  <button type="button" class="drawer-backdrop" aria-label="Sluiten" onclick={close}></button>
  <aside class="drawer-panel" class:wide aria-labelledby="drawer-title">
    <div class="drawer-head">
      <h2 id="drawer-title">{title}</h2>
      <button type="button" class="drawer-close" aria-label="Sluiten" onclick={close}>×</button>
    </div>
    <div class="drawer-body">
      {@render children?.()}
    </div>
    {#if footer}
      <div class="drawer-foot">
        {@render footer()}
      </div>
    {/if}
  </aside>
{/if}
