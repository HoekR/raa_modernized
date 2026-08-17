<script lang="ts">
  import { PAGE_SIZE } from '$lib/period';

  let {
    total,
    offset,
    onpage,
  }: {
    total: number;
    offset: number;
    onpage: (offset: number) => void;
  } = $props();

  const start = $derived(total ? offset + 1 : 0);
  const end = $derived(Math.min(offset + PAGE_SIZE, total));
</script>

{#if total}
  <div class="pager">
    <span>{start}–{end} van {total}</span>
    <button type="button" disabled={offset <= 0} onclick={() => onpage(Math.max(0, offset - PAGE_SIZE))}
      >Vorige</button
    >
    <button
      type="button"
      disabled={offset + PAGE_SIZE >= total}
      onclick={() => onpage(offset + PAGE_SIZE)}>Volgende</button
    >
  </div>
{/if}

<style>
  .pager {
    display: flex;
    gap: 0.65rem;
    align-items: center;
    margin: 0.65rem 0;
    font-size: 0.875rem;
    color: var(--raa-ink-muted);
  }
  button {
    padding: 0.3rem 0.7rem;
    border: 1px solid var(--raa-line-strong);
    background: var(--raa-surface);
    border-radius: var(--raa-radius);
    color: var(--raa-ink);
    transition: border-color var(--raa-ease), background var(--raa-ease);
  }
  button:hover:not(:disabled) {
    border-color: var(--raa-accent);
    background: var(--raa-accent-softer);
  }
</style>
