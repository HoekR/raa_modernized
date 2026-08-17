<script lang="ts">
  import { loadStands } from '$lib/search';

  let {
    standIds = $bindable([] as number[]),
    adelOnly = $bindable(false),
  }: {
    standIds?: number[];
    adelOnly?: boolean;
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
  <p class="hint">Stand (max. 5):</p>
  <div class="stands">
    {#each stands as s}
      <label>
        <input
          type="checkbox"
          checked={standIds.includes(s.id)}
          onchange={(e) => toggleStand(s.id, (e.currentTarget as HTMLInputElement).checked)}
        />
        {s.naam}
      </label>
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
</style>
