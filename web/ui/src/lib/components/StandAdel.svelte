<script lang="ts">
  import { loadStands } from '$lib/search';
  import type { FacetValue } from '$lib/period';

  let {
    standIds = $bindable([] as number[]),
    adelOnly = $bindable(false),
    /** When set, only show stands that appear in the current facet result (count > 0). */
    standFacets = null as FacetValue[] | null,
  }: {
    standIds?: number[];
    adelOnly?: boolean;
    standFacets?: FacetValue[] | null;
  } = $props();

  let stands = $state<{ id: number; naam: string }[]>([]);

  $effect(() => {
    loadStands()
      .then((rows) => {
        stands = rows;
      })
      .catch(() => {
        stands = [];
      });
  });

  const visibleStands = $derived.by(() => {
    if (!standFacets) return stands;
    const allowed = new Set(standFacets.map((f) => Number(f.key)).filter((n) => !Number.isNaN(n)));
    // Keep selected stands visible even if temporarily missing from facets.
    for (const id of standIds) allowed.add(id);
    return stands.filter((s) => allowed.has(s.id));
  });

  function toggleStand(id: number, checked: boolean) {
    if (checked) {
      if (standIds.length >= 5) return;
      standIds = [...standIds, id];
    } else {
      standIds = standIds.filter((x) => x !== id);
    }
  }
</script>

<fieldset class="box">
  <legend>Stand en adel</legend>
  <label class="adel">
    <input type="checkbox" bind:checked={adelOnly} />
    Alleen adel
  </label>
  <p class="hint">Stand (max. 5){standFacets ? ' — alleen in huidige selectie' : ''}:</p>
  <div class="stands">
    {#each visibleStands as s}
      <label>
        <input
          type="checkbox"
          checked={standIds.includes(s.id)}
          onchange={(e) => toggleStand(s.id, (e.currentTarget as HTMLInputElement).checked)}
        />
        {s.naam}
      </label>
    {:else}
      <p class="hint empty">Geen standen in deze periode/selectie</p>
    {/each}
  </div>
</fieldset>

<style>
  .adel {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 0.45rem;
    margin-bottom: 0.5rem;
    font-weight: 400;
    color: var(--raa-ink);
  }
  .stands {
    display: grid;
    grid-columns: repeat(2, 1fr);
    grid-template-columns: repeat(2, 1fr);
    gap: 0.25rem 1rem;
    font-size: 0.9rem;
  }
  .stands label {
    flex-direction: row;
    align-items: center;
    gap: 0.4rem;
    font-weight: 400;
    color: var(--raa-ink);
  }
  .empty {
    grid-column: 1 / -1;
    margin: 0;
  }
</style>
