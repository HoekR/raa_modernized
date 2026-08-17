<script lang="ts">
  export type Chip = { key: string; label: string; clear: () => void };

  let {
    chips,
    onClearAll,
  }: {
    chips: Chip[];
    onClearAll?: () => void;
  } = $props();
</script>

{#if chips.length}
  <ul class="active-chips">
    {#each chips as chip}
      <li>
        {chip.label}
        <button type="button" class="x" onclick={chip.clear} aria-label="verwijder">×</button>
      </li>
    {/each}
    {#if onClearAll}
      <li class="clear-all">
        <button type="button" onclick={onClearAll}>Wis filters</button>
      </li>
    {/if}
  </ul>
{/if}
