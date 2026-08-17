<script lang="ts">
  import { suggestField } from '$lib/search';
  import { MAX_CHIPS, type SuggestItem } from '$lib/period';

  let {
    label,
    field,
    selected = $bindable([] as SuggestItem[]),
    match = $bindable('any' as 'any' | 'all'),
    showMatch = true,
  }: {
    label: string;
    field: string;
    selected?: SuggestItem[];
    match?: 'any' | 'all';
    showMatch?: boolean;
  } = $props();

  let q = $state('');
  let suggestions = $state<SuggestItem[]>([]);
  let open = $state(false);
  let timer: ReturnType<typeof setTimeout> | undefined;

  function onInput() {
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
    if (selected.some((s) => s.id === item.id)) return;
    if (selected.length >= MAX_CHIPS) return;
    selected = [...selected, item];
    q = '';
    suggestions = [];
    open = false;
  }

  function remove(id: number) {
    selected = selected.filter((s) => s.id !== id);
  }
</script>

<div class="chip-picker">
  <label>
    {label}
    <input
      type="text"
      bind:value={q}
      oninput={onInput}
      onfocus={() => {
        if (suggestions.length) open = true;
      }}
      autocomplete="off"
      placeholder="zoek…"
    />
  </label>
  {#if open}
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
      <li>
        {item.naam}
        <button type="button" class="x" onclick={() => remove(item.id)} aria-label="verwijder">×</button>
      </li>
    {/each}
  </ul>
  {#if showMatch}
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
    overflow-y: auto;
    width: 100%;
    box-shadow: var(--raa-shadow);
  }
  .suggest button {
    display: block;
    width: 100%;
    text-align: left;
    border: 0;
    background: transparent;
    padding: 0.4rem 0.55rem;
    cursor: pointer;
    font: inherit;
  }
  .suggest button:hover {
    background: var(--raa-accent-softer);
  }
  .empty {
    padding: 0.4rem 0.55rem;
    color: var(--raa-ink-muted);
    font-style: italic;
  }
  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    list-style: none;
    margin: 0.45rem 0 0;
    padding: 0;
  }
  .chips li {
    background: var(--raa-accent-soft);
    border: 1px solid var(--raa-chip-border);
    border-radius: 999px;
    padding: 0.15rem 0.5rem;
    font-size: 0.82rem;
  }
  .x {
    border: 0;
    background: transparent;
    cursor: pointer;
    margin-left: 0.15rem;
  }
  .match {
    display: flex;
    gap: 0.75rem;
    margin-top: 0.4rem;
    font-size: 0.85rem;
  }
  .match label {
    flex-direction: row;
    align-items: center;
    gap: 0.35rem;
    font-weight: 400;
    color: var(--raa-ink);
  }
</style>
