<script lang="ts">
  import FacetBarChart from '$lib/components/FacetBarChart.svelte';
  import { orderPeriodFacets, periodBarColor } from '$lib/facetChart';
  import type { FacetValue } from '$lib/period';

  let {
    values = [],
    onselect,
  }: {
    values?: FacetValue[];
    onselect?: (value: FacetValue) => void;
  } = $props();

  const ordered = $derived(orderPeriodFacets(values));
</script>

<FacetBarChart
  title="Verdeling per periode"
  values={ordered}
  maxBars={4}
  colorForKey={periodBarColor}
  {onselect}
/>
