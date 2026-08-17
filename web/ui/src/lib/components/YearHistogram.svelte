<script lang="ts">
  import { periodBarColor } from '$lib/facetChart';
  import {
    PERIOD_KEYS,
    periodShortLabel,
    shouldShowTimelineLabel,
    stackedTimelineNote,
    stackSegmentFlex,
    timelineBarHeight,
    timelineBinLabel,
    timelineStackTotal,
    undatedNoteForEntity,
    type TimelineBin,
    type YearCount,
  } from '$lib/yearHistogram';

  let {
    title,
    bins = [],
    bin = 'year',
    compact = false,
    wide = false,
    stacked = false,
    undated = 0,
    entity = 'personen',
    includeShadowDates = true,
    onselect,
  }: {
    title: string;
    bins?: YearCount[];
    bin?: TimelineBin;
    compact?: boolean;
    /** Wider bar track (overview) — scroll instead of squeezing labels. */
    wide?: boolean;
    stacked?: boolean;
    undated?: number;
    entity?: 'personen' | 'aanstellingen';
    includeShadowDates?: boolean;
    onselect?: (year: number, period?: string) => void;
  } = $props();

  const maxCount = $derived(Math.max(...bins.map((b) => timelineStackTotal(b)), 0));
  const undatedNote = $derived(undatedNoteForEntity(entity, undated, includeShadowDates));
  const shortDecadeLabels = $derived(bin === 'decade' && bins.length > 15);
  const maxVisibleLabels = $derived(wide ? 14 : 12);

  function barLabel(index: number, year: number): string {
    return timelineBinLabel(year, bin, { shortDecade: shortDecadeLabels });
  }

  function showLabel(index: number): boolean {
    return shouldShowTimelineLabel(index, bins.length, maxVisibleLabels);
  }
</script>

<section class="year-histogram" class:compact class:wide>
  <h4>{title}</h4>
  {#if stacked}
    <ul class="legend" aria-label="Periodes">
      {#each PERIOD_KEYS as pk}
        <li>
          <span class="swatch" style:background={periodBarColor(pk)}></span>
          {periodShortLabel(pk)}
        </li>
      {/each}
    </ul>
  {/if}
  {#if bins.length === 0}
    <p class="empty">Geen gedateerde treffers voor deze grafiek.</p>
  {:else}
    <div class="bars" role="img" aria-label={title}>
      {#each bins as b, i (b.year)}
        {@const stackTotal = timelineStackTotal(b)}
        {@const h = timelineBarHeight(stackTotal, maxCount)}
        {@const label = barLabel(i, b.year)}
        {@const labelVisible = !compact && showLabel(i)}
        {#if stacked && b.by_period}
          <div class="bar-col">
            <div class="bar-stack" style:height="{Math.max(h, 4)}%" title="{label}: {stackTotal}">
              {#each PERIOD_KEYS as pk}
                {@const seg = b.by_period[pk] ?? 0}
                {#if seg > 0}
                  {#if onselect}
                    <button
                      type="button"
                      class="seg-btn"
                      style:flex={stackSegmentFlex(seg, stackTotal)}
                      style:background={periodBarColor(pk)}
                      title="{periodShortLabel(pk)} {label}: {seg}"
                      aria-label="{periodShortLabel(pk)} {label}, {seg}"
                      onclick={() => onselect(b.year, pk)}
                    ></button>
                  {:else}
                    <span
                      class="seg"
                      style:flex={stackSegmentFlex(seg, stackTotal)}
                      style:background={periodBarColor(pk)}
                    ></span>
                  {/if}
                {/if}
              {/each}
            </div>
            {#if labelVisible}
              <span class="bar-lab">{label}</span>
            {/if}
          </div>
        {:else if onselect}
          <button
            type="button"
            class="bar-btn"
            title="{label}: {b.count}"
            aria-label="{label}, {b.count} treffers"
            onclick={() => onselect(b.year)}
          >
            <span class="bar" style:height="{Math.max(h, 4)}%"></span>
            {#if labelVisible}
              <span class="bar-lab">{label}</span>
            {/if}
          </button>
        {:else}
          <div class="bar-static" title="{label}: {b.count}">
            <span class="bar" style:height="{Math.max(h, 4)}%"></span>
            {#if labelVisible}
              <span class="bar-lab">{label}</span>
            {/if}
          </div>
        {/if}
      {/each}
    </div>
    {#if stacked}
      <p class="stacked-note">{stackedTimelineNote()}</p>
    {/if}
    {#if undatedNote}
      <p class="undated">{undatedNote}</p>
    {/if}
  {/if}
</section>

<style>
  .year-histogram {
    margin-bottom: 1rem;
  }
  .year-histogram.compact {
    margin: 0.5rem 0 0.85rem;
    padding: 0.55rem 0.65rem;
    background: var(--raa-paper);
    border: 1px solid var(--raa-line);
    border-radius: var(--raa-radius);
  }
  h4 {
    margin: 0 0 0.4rem;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--raa-ink-faint);
    font-weight: 600;
  }
  .compact h4 {
    margin-bottom: 0.35rem;
  }
  .legend {
    list-style: none;
    margin: 0 0 0.45rem;
    padding: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem 0.65rem;
    font-size: 0.68rem;
    color: var(--raa-ink-faint);
  }
  .legend li {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
  }
  .swatch {
    width: 0.55rem;
    height: 0.55rem;
    border-radius: 2px;
    flex-shrink: 0;
  }
  .bars {
    display: flex;
    align-items: flex-end;
    gap: 2px;
    height: 4.5rem;
    overflow-x: auto;
    padding-bottom: 0.15rem;
  }
  .compact .bars {
    height: 3.25rem;
  }
  .bar-col,
  .bar-btn,
  .bar-static {
    flex: 1 0 0.45rem;
    min-width: 0.45rem;
    max-width: 1.1rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-end;
    height: 100%;
  }
  .bar-btn {
    border: 0;
    background: transparent;
    padding: 0;
    cursor: pointer;
  }
  .bar-stack {
    display: flex;
    flex-direction: column-reverse;
    justify-content: flex-start;
    width: 100%;
    min-height: 2px;
    border-radius: 2px 2px 0 0;
    overflow: hidden;
  }
  .seg,
  .seg-btn {
    display: block;
    width: 100%;
    min-height: 1px;
    border: 0;
    padding: 0;
  }
  .seg-btn {
    cursor: pointer;
    opacity: 1;
  }
  .seg-btn:hover {
    filter: brightness(1.08);
  }
  .bar {
    display: block;
    width: 100%;
    min-height: 2px;
    background: var(--raa-accent);
    border-radius: 2px 2px 0 0;
  }
  .bar-btn:hover .bar {
    background: var(--raa-accent-bright);
  }
  .bar-lab {
    margin-top: 0.2rem;
    font-size: 0.62rem;
    color: var(--raa-ink-faint);
    writing-mode: vertical-rl;
    transform: rotate(180deg);
    max-height: 2.5rem;
    overflow: hidden;
    line-height: 1.1;
  }
  .wide .bars {
    height: 5.5rem;
    padding-bottom: 2.25rem;
    align-items: stretch;
  }
  .wide .bar-col,
  .wide .bar-btn,
  .wide .bar-static {
    flex: 0 0 1.35rem;
    min-width: 1.35rem;
    max-width: none;
    justify-content: flex-end;
  }
  .wide .bar-lab {
    writing-mode: horizontal-tb;
    transform: none;
    max-height: none;
    overflow: visible;
    text-align: center;
    width: 100%;
  }
  .empty,
  .undated,
  .stacked-note {
    margin: 0.25rem 0 0;
    font-size: 0.75rem;
    color: var(--raa-ink-faint);
  }
</style>
