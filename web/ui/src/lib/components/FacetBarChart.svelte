<script lang="ts">
  import { barWidthPct, topFacetBars } from '$lib/facetChart';
  import type { FacetValue } from '$lib/period';

  let {
    title,
    values = [],
    maxBars = 8,
    colorForKey,
    onselect,
  }: {
    title: string;
    values?: FacetValue[];
    maxBars?: number;
    colorForKey?: (key: string) => string;
    onselect?: (value: FacetValue) => void;
  } = $props();

  const { shown, rest } = $derived(topFacetBars(values, maxBars));
  const maxCount = $derived(Math.max(...shown.map((v) => v.count), 0));
</script>

<section class="facet-chart">
  <h4>{title}</h4>
  {#if shown.length === 0}
    <p class="empty">Geen waarden in deze selectie</p>
  {:else}
    <ul>
      {#each shown as val (val.key)}
        {@const pct = barWidthPct(val.count, maxCount)}
        {@const fill = colorForKey?.(val.key) ?? 'var(--raa-accent)'}
        <li>
          {#if onselect}
            <button type="button" class="row" title={val.label} onclick={() => onselect(val)}>
              <span class="lab">{val.label}</span>
              <span class="bar-wrap" aria-hidden="true">
                <span class="bar" style:width="{pct}%" style:background={fill}></span>
              </span>
              <span class="n">{val.count}</span>
            </button>
          {:else}
            <div class="row static" title={val.label}>
              <span class="lab">{val.label}</span>
              <span class="bar-wrap" aria-hidden="true">
                <span class="bar" style:width="{pct}%" style:background={fill}></span>
              </span>
              <span class="n">{val.count}</span>
            </div>
          {/if}
        </li>
      {/each}
    </ul>
    {#if rest > 0}
      <p class="more">+{rest} meer onder Verfijnen</p>
    {/if}
  {/if}
</section>

<style>
  .facet-chart {
    margin-bottom: 1.1rem;
  }
  h4 {
    margin: 0 0 0.45rem;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--raa-ink-faint);
    font-weight: 600;
  }
  ul {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .row {
    display: grid;
    grid-template-columns: minmax(0, 7.5rem) 1fr auto;
    gap: 0.45rem;
    align-items: center;
    width: 100%;
    text-align: left;
    border: 0;
    background: transparent;
    padding: 0.22rem 0.15rem;
    border-radius: var(--raa-radius);
    font: inherit;
    color: inherit;
    cursor: default;
  }
  button.row {
    cursor: pointer;
    transition: background var(--raa-ease);
  }
  button.row:hover {
    background: var(--raa-accent-softer);
  }
  .lab {
    font-size: 0.78rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .bar-wrap {
    height: 0.55rem;
    background: var(--raa-line);
    border-radius: 2px;
    overflow: hidden;
    min-width: 0;
  }
  .bar {
    display: block;
    height: 100%;
    min-width: 0;
    border-radius: 2px;
    transition: width 0.2s ease;
  }
  .n {
    font-size: 0.78rem;
    color: var(--raa-ink-faint);
    font-variant-numeric: tabular-nums;
    min-width: 2rem;
    text-align: right;
  }
  .more,
  .empty {
    margin: 0.25rem 0 0;
    font-size: 0.75rem;
    color: var(--raa-ink-faint);
  }
</style>
