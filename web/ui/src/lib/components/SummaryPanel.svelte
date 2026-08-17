<script lang="ts">
  import FacetSummary from '$lib/components/FacetSummary.svelte';
  import MovablePanel from '$lib/components/MovablePanel.svelte';
  import type { FacetValue, PeriodMode } from '$lib/period';
  import type { TimelineMeta, YearCount } from '$lib/yearHistogram';

  let {
    open = $bindable(false),
    entity,
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
    open?: boolean;
    entity: 'personen' | 'aanstellingen';
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
</script>

<MovablePanel bind:open storageKey="raa-summary-{entity}" title="Samenvatting">
  <FacetSummary
    {entity}
    {facets}
    {periodMode}
    {hasSearched}
    {total}
    {timeline}
    {timelineMeta}
    {includeShadowDates}
    {onselect}
    {onTimelineSelect}
  />
</MovablePanel>
