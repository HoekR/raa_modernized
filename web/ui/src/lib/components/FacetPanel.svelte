<script lang="ts">
  import type { FacetValue } from '$lib/period';

  const LABELS: Record<string, string> = {
    period: 'Periode',
    stand: 'Stand',
    adel: 'Adel',
    functie: 'Functie',
    instelling: 'Instelling',
    provincie: 'Provinciaal',
    regio: 'Regionaal',
    lokaal: 'Lokaal',
  };

  const ORDER = [
    'period',
    'adel',
    'stand',
    'functie',
    'instelling',
    'provincie',
    'regio',
    'lokaal',
  ];

  let {
    facets = {},
    selectedKeys = {},
    ontoggle,
  }: {
    facets?: Record<string, FacetValue[]>;
    selectedKeys?: Record<string, string[]>;
    ontoggle: (dimension: string, value: FacetValue) => void;
  } = $props();

  function isSelected(dim: string, key: string): boolean {
    return (selectedKeys[dim] ?? []).includes(key);
  }

  function dims(): string[] {
    return ORDER.filter((d) => (facets[d] ?? []).length > 0);
  }
</script>

<aside class="facets">
  <h3>Verfijnen</h3>
  {#each dims() as dim}
    <section class="dim">
      <h4>{LABELS[dim] ?? dim}</h4>
      <ul>
        {#each facets[dim] ?? [] as val}
          <li>
            <button
              type="button"
              class:active={isSelected(dim, val.key)}
              onclick={() => ontoggle(dim, val)}
            >
              <span class="lab">{val.label}</span>
              <span class="n">{val.count}</span>
            </button>
          </li>
        {/each}
      </ul>
    </section>
  {/each}
</aside>

<style>
  .facets {
    font-size: 0.875rem;
    background: var(--raa-surface);
    border: 1px solid var(--raa-line);
    border-radius: var(--raa-radius);
    padding: 0.85rem 0.75rem;
    position: sticky;
    top: 0.75rem;
    max-height: calc(100vh - 1.5rem);
    overflow: auto;
    box-shadow: var(--raa-shadow);
  }
  h3 {
    margin: 0 0 0.85rem;
    font-size: 0.95rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--raa-accent-bright);
  }
  .dim {
    margin-bottom: 0.95rem;
  }
  h4 {
    margin: 0 0 0.3rem;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--raa-ink-faint);
    font-weight: 600;
  }
  ul {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  button {
    display: flex;
    justify-content: space-between;
    gap: 0.5rem;
    width: 100%;
    text-align: left;
    border: 0;
    background: transparent;
    padding: 0.28rem 0.35rem;
    border-radius: var(--raa-radius);
    cursor: pointer;
    font: inherit;
    color: inherit;
    transition: background var(--raa-ease);
  }
  button:hover {
    background: var(--raa-accent-softer);
  }
  button.active {
    font-weight: 600;
    background: var(--raa-accent-soft);
  }
  .lab {
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .n {
    color: var(--raa-ink-faint);
    font-variant-numeric: tabular-nums;
    flex-shrink: 0;
  }
  button.active .n {
    color: var(--raa-ink-muted);
  }
</style>
