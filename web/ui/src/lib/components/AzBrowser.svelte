<script lang="ts">
  import { browseAz } from '$lib/search';
  import { periodKey } from '$lib/period';

  let {
    entity,
    letter = $bindable(null as string | null),
    onchange,
  }: {
    entity: 'personen' | 'instellingen' | 'functies';
    letter?: string | null;
    onchange?: () => void;
  } = $props();

  let counts = $state<Record<string, number>>({});

  async function refresh() {
    try {
      const data = await browseAz(entity, { letter: null, size: 1 });
      const next: Record<string, number> = {};
      for (const row of data.letters || []) next[row.letter] = row.count;
      counts = next;
    } catch {
      counts = {};
    }
  }

  $effect(() => {
    void $periodKey;
    refresh();
  });

  function select(next: string | null) {
    letter = next;
    onchange?.();
  }

  const letters = [...'ABCDEFGHIJKLMNOPQRSTUVWXYZ', '#'];
</script>

<div class="az">
  <button type="button" class:active={letter == null} onclick={() => select(null)}>Alles</button>
  {#each letters as L}
    <button
      type="button"
      class:active={letter === L}
      disabled={!counts[L]}
      title={counts[L] ? `${counts[L]} treffers` : 'geen'}
      onclick={() => select(L)}>{L}</button
    >
  {/each}
</div>

<style>
  .az {
    display: flex;
    flex-wrap: wrap;
    gap: 0.3rem;
    margin: 0.5rem 0 1rem;
  }
  button {
    min-width: 1.85rem;
    padding: 0.3rem 0.4rem;
    border: 1px solid var(--raa-line-strong);
    background: var(--raa-surface);
    border-radius: var(--raa-radius);
    cursor: pointer;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--raa-ink);
    transition: background var(--raa-ease), border-color var(--raa-ease), color var(--raa-ease);
  }
  button:hover:not(:disabled) {
    border-color: var(--raa-accent);
  }
  button:disabled {
    opacity: 0.3;
    cursor: default;
  }
  button.active {
    background: var(--raa-ink);
    color: #fff;
    border-color: var(--raa-ink);
  }
</style>
