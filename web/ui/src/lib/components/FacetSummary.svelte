<script lang="ts">
  import FacetBarChart from '$lib/components/FacetBarChart.svelte';
  import PeriodBarChart from '$lib/components/PeriodBarChart.svelte';
  import YearHistogram from '$lib/components/YearHistogram.svelte';
  import type { FacetValue, PeriodMode } from '$lib/period';
  import {
    timelineChartTitle,
    type TimelineBin,
    type TimelineMeta,
    type YearCount,
  } from '$lib/yearHistogram';

  let {
    entity = 'personen',
    facets = {},
    periodMode = 'scoped',
    hasSearched = false,
    total = null,
    timeline = [],
    timelineMeta = null,
    includeShadowDates = true,
    onselect,
    onTimelineSelect,
  }: {
    entity?: 'personen' | 'aanstellingen';
    facets?: Record<string, FacetValue[]>;
    periodMode?: PeriodMode;
    hasSearched?: boolean;
    total?: number | null;
    timeline?: YearCount[];
    timelineMeta?: TimelineMeta | null;
    includeShadowDates?: boolean;
    onselect: (dimension: string, value: FacetValue) => void;
    onTimelineSelect?: (year: number, period?: string) => void;
  } = $props();

  const timelineTitle = $derived(timelineChartTitle(entity, includeShadowDates));
  const timelineBin = $derived((timelineMeta?.bin ?? 'year') as TimelineBin);
</script>

<div class="facet-summary">
  {#if !hasSearched}
    <p class="hint">Zoek eerst om een samenvatting te zien.</p>
  {:else if total === 0}
    <p class="hint">Geen treffers om samen te vatten.</p>
  {:else}
    {#if timeline.length > 0 && timelineMeta}
      <YearHistogram
        title={timelineTitle}
        bins={timeline}
        bin={timelineBin}
        wide
        stacked={timelineMeta.stacked ?? false}
        {entity}
        {includeShadowDates}
        undated={timelineMeta.undated}
        onselect={onTimelineSelect}
      />
    {/if}
    {#if entity === 'personen' && periodMode === 'overall'}
      <PeriodBarChart values={facets.period ?? []} onselect={(v) => onselect('period', v)} />
    {/if}
    {#if (facets.functie ?? []).length > 0}
      <FacetBarChart
        title="Functie"
        values={facets.functie}
        onselect={(v) => onselect('functie', v)}
      />
    {/if}
    {#if (facets.instelling ?? []).length > 0}
      <FacetBarChart
        title="Instelling"
        values={facets.instelling}
        onselect={(v) => onselect('instelling', v)}
      />
    {/if}
    {#if (facets.stand ?? []).length > 0}
      <FacetBarChart
        title="Stand"
        values={facets.stand}
        onselect={(v) => onselect('stand', v)}
      />
    {/if}
    <p class="footnote">Grafieken tonen maximaal 8 waarden; alle filters staan in Verfijnen.</p>
  {/if}
</div>

<style>
  .facet-summary {
    font-size: 0.875rem;
  }
  .hint,
  .footnote {
    margin: 0;
    font-size: 0.8rem;
    color: var(--raa-ink-faint);
  }
  .footnote {
    margin-top: 0.5rem;
    font-size: 0.75rem;
  }
</style>
