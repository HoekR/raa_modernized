<script lang="ts">
  import { PAGE_SIZE_OPTIONS } from '$lib/period';

  let {
    total,
    offset,
    pageSize = 100,
    onpage,
    onPageSizeChange,
  }: {
    total: number;
    offset: number;
    pageSize?: number;
    onpage: (offset: number) => void;
    onPageSizeChange?: (size: number) => void;
  } = $props();

  const start = $derived(total ? offset + 1 : 0);
  const end = $derived(Math.min(offset + pageSize, total));
</script>

{#if total}
  <div class="pager">
    <span>{start}–{end} van {total}</span>
    {#if onPageSizeChange}
      <label class="page-size">
        Per pagina
        <select
          value={pageSize}
          onchange={(e) => onPageSizeChange(Number((e.currentTarget as HTMLSelectElement).value))}
        >
          {#each PAGE_SIZE_OPTIONS as n}
            <option value={n}>{n}</option>
          {/each}
        </select>
      </label>
    {/if}
    <button type="button" disabled={offset <= 0} onclick={() => onpage(Math.max(0, offset - pageSize))}
      >Vorige</button
    >
    <button
      type="button"
      disabled={offset + pageSize >= total}
      onclick={() => onpage(offset + pageSize)}>Volgende</button
    >
  </div>
{/if}

<style>
  .pager {
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
    align-items: center;
    margin: 0.65rem 0;
    font-size: 0.875rem;
    color: var(--raa-ink-muted);
  }
  .page-size {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.8rem;
    color: var(--raa-ink-faint);
  }
  select {
    font: inherit;
    font-size: 0.85rem;
    color: var(--raa-ink);
    padding: 0.2rem 0.35rem;
    border: 1px solid var(--raa-line-strong);
    border-radius: var(--raa-radius);
    background: var(--raa-surface);
  }
  button {
    padding: 0.3rem 0.7rem;
    border: 1px solid var(--raa-line-strong);
    background: var(--raa-surface);
    border-radius: var(--raa-radius);
    color: var(--raa-ink);
    transition:
      border-color var(--raa-ease),
      background var(--raa-ease);
  }
  button:hover:not(:disabled) {
    border-color: var(--raa-accent);
    background: var(--raa-accent-softer);
  }
</style>
