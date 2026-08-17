<script lang="ts">
  import { periodKey, type PeriodCount } from '$lib/period';

  let { periods = [] }: { periods?: PeriodCount[] } = $props();
</script>

<label class="period-select">
  Periode
  <select
    value={$periodKey}
    onchange={(e) => periodKey.set((e.currentTarget as HTMLSelectElement).value)}
  >
    {#each periods as p}
      <option value={p.key}>{p.label} ({p.count})</option>
    {/each}
    <option value="all">Alle perioden</option>
  </select>
</label>

<style>
  .period-select {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }
  select {
    min-width: 14rem;
    text-transform: none;
    letter-spacing: normal;
    font-weight: 500;
  }
</style>
