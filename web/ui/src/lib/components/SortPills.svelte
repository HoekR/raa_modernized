<script lang="ts">
  let {
    options,
    sort = $bindable(''),
    sortDir = $bindable<'asc' | 'desc'>('asc'),
    onchange,
  }: {
    options: [string, string][];
    sort?: string;
    sortDir?: 'asc' | 'desc';
    onchange?: () => void;
  } = $props();

  function toggle(key: string) {
    if (sort === key) {
      sortDir = sortDir === 'asc' ? 'desc' : 'asc';
    } else {
      sort = key;
      sortDir = 'asc';
    }
    onchange?.();
  }
</script>

<div class="sort" aria-label="Sorteer">
  <span class="sort-label">Sorteer:</span>
  {#each options as [key, label]}
    <button
      type="button"
      class:active={sort === key}
      class:desc={sort === key && sortDir === 'desc'}
      class:asc={sort === key && sortDir === 'asc'}
      title={sort === key
        ? sortDir === 'asc'
          ? 'Oplopend — klik voor aflopend'
          : 'Aflopend — klik voor oplopend'
        : 'Sorteer oplopend'}
      onclick={() => toggle(key)}
    >
      {label}{sort === key ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''}
    </button>
  {/each}
</div>
