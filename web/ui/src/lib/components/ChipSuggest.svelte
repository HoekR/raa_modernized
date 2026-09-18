<script lang="ts">
  import { suggestField } from '$lib/search';
  import { MAX_CHIPS, type SuggestItem } from '$lib/period';

  let {
    label,
    field,
    selected = $bindable([] as SuggestItem[]),
    match = $bindable('any' as 'any' | 'all'),
    showMatch = true,
    lockedIds = [] as number[],
    onUnlock,
  }: {
    label: string;
    field: string;
    selected?: SuggestItem[];
    match?: 'any' | 'all';
    showMatch?: boolean;
    /** Chip ids that cannot be removed until unlocked. */
    lockedIds?: number[];
    onUnlock?: () => void;
  } = $props();

  let q = $state('');
  let suggestions = $state<SuggestItem[]>([]);
  let open = $state(false);
  let timer: ReturnType<typeof setTimeout> | undefined;

  const locked = $derived(lockedIds.length > 0);

  function onInput() {
    if (locked) return;
    clearTimeout(timer);
    timer = setTimeout(async () => {
      const text = q.trim();
      if (text.length < 2) {
        suggestions = [];
        open = false;
        return;
      }
      suggestions = await suggestField(field, text);
      open = true;
    }, 200);
  }

  function pick(item: SuggestItem) {
    if (locked) return;
    if (selected.some((s) => s.id === item.id)) return;
    if (selected.length >= MAX_CHIPS) return;
    selected = [...selected, item];
    q = '';
    suggestions = [];
    open = false;
  }

  function remove(id: number) {
    if (lockedIds.includes(id)) return;
    selected = selected.filter((s) => s.id !== id);
  }
</script>

<div class="chip-picker" class:locked>
  <label>
    {label}
    <input
      type="text"
      bind:value={q}
      oninput={onInput}
      onfocus={() => {
        if (!locked && suggestions.length) open = true;
      }}
      autocomplete="off"
      placeholder={locked ? 'vergrendeld…' : 'zoek…'}
      disabled={locked}
    />
  </label>
  {#if open && !locked}
    <ul class="suggest">
      {#if !suggestions.length}
        <li class="empty">Geen suggesties in deze periode</li>
      {:else}
        {#each suggestions as item}
          <li>
            <button type="button" onclick={() => pick(item)}>{item.naam}</button>
          </li>
        {/each}
      {/if}
    </ul>
  {/if}
  <ul class="chips">
    {#each selected as item}
      <li class:chip-locked={lockedIds.includes(item.id)}>
        {item.naam}
        {#if lockedIds.includes(item.id)}
          <span class="lock-tag" title="Vergrendeld vanuit detail">vast</span>
        {:else}
          <button type="button" class="x" onclick={() => remove(item.id)} aria-label="verwijder">×</button>
        {/if}
      </li>
    {/each}
  </ul>
  {#if locked && onUnlock}
    <button type="button" class="unlock" onclick={onUnlock}>Ontgrendel</button>
  {/if}
  {#if showMatch && !locked}
    <div class="match">
      <label><input type="radio" bind:group={match} value="any" /> of</label>
      <label><input type="radio" bind:group={match} value="all" /> en</label>
    </div>
  {/if}
</div>

<style>
  .chip-picker {
    position: relative;
  }
  label {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.875rem;
  }
  input[type='text'] {
    padding: 0.45rem 0.55rem;
  }
  input:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
  .suggest {
    position: absolute;
    z-index: 20;
    background: var(--raa-surface);
    border: 1px solid var(--raa-line-strong);
    border-radius: var(--raa-radius);
    list-style: none;
    margin: 0;
    padding: 0;
    max-height: 12rem;
    overflow: auto;
    width: 100%;
    box-shadow: 0 4px 12px rgb(0 0 0 / 0.08);
  }
  .suggest li button {
    display: block;
    width: 100%;
    text-align: left;
    border: 0;
    background: transparent;
    padding: 0.4rem 0.55rem;
    cursor: pointer;
  }
  .suggest li button:hover {
    background: var(--raa-accent-softer);
  }
  .suggest .empty {
    padding: 0.45rem 0.55rem;
    color: var(--raa-ink-muted);
    font-size: 0.85rem;
  }
  .chips {
    list-style: none;
    margin: 0.4rem 0 0;
    padding: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
  }
  .chips li {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    background: var(--raa-accent-softer);
    border: 1px solid var(--raa-line);
    border-radius: var(--raa-radius);
    padding: 0.15rem 0.4rem;
    font-size: 0.82rem;
  }
  .chips li.chip-locked {
    border-color: var(--raa-accent-bright);
  }
  .lock-tag {
    font-size: 0.7rem;
  }
  .x {
    border: 0;
    background: transparent;
    cursor: pointer;
    font-size: 1rem;
    line-height: 1;
    padding: 0 0.15rem;
    color: var(--raa-ink-muted);
  }
  .unlock {
    margin-top: 0.35rem;
    font-size: 0.8rem;
    padding: 0.25rem 0.5rem;
    cursor: pointer;
  }
  .match {
    display: flex;
    gap: 0.75rem;
    margin-top: 0.35rem;
    font-size: 0.82rem;
  }
  .match label {
    flex-direction: row;
    align-items: center;
    gap: 0.3rem;
    font-weight: 400;
  }
</style>
