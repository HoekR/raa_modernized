<script lang="ts">
  import AzBrowser from '$lib/components/AzBrowser.svelte';
  import Pagination from '$lib/components/Pagination.svelte';
  import { PAGE_SIZE, periodKey } from '$lib/period';
  import { browseAz, searchEntity } from '$lib/search';

  let q = $state('');
  let letter = $state<string | null>(null);
  let offset = $state(0);
  let total = $state<number | null>(null);
  let hits = $state<Record<string, unknown>[]>([]);
  let error = $state<string | null>(null);
  let loading = $state(false);

  async function runSearch() {
    loading = true;
    error = null;
    try {
      if (letter && !q.trim()) {
        const data = await browseAz('functies', { letter, from: offset, size: PAGE_SIZE });
        total = data.total;
        hits = data.hits;
      } else {
        const data = await searchEntity('functies', {
          q: q.trim() || null,
          from: offset,
          size: PAGE_SIZE,
        });
        total = data.total;
        hits = data.hits;
      }
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
      total = null;
      hits = [];
    } finally {
      loading = false;
    }
  }

  function submit() {
    letter = null;
    offset = 0;
    runSearch();
  }

  $effect(() => {
    void $periodKey;
    offset = 0;
    runSearch();
  });
</script>

<section>
  <h2>Functies zoeken</h2>

  <form
    class="basic"
    onsubmit={(e) => {
      e.preventDefault();
      submit();
    }}
  >
    <label class="q">
      Naam (wildcards * ?)
      <input bind:value={q} placeholder="bijv. burgemeester*" />
    </label>
    <button type="submit" disabled={loading}>{loading ? 'Zoeken…' : 'Zoeken'}</button>
  </form>

  <p class="hint az-hint">Of blader A–Z (periode-scoped):</p>
  <AzBrowser
    entity="functies"
    bind:letter
    onchange={() => {
      q = '';
      offset = 0;
      runSearch();
    }}
  />

  {#if error}
    <p class="err">{error}</p>
  {/if}
  {#if total !== null}
    <div class="results-panel">
      <p class="count">{total} treffers</p>
      <Pagination {total} {offset} onpage={(o) => { offset = o; runSearch(); }} />
      <table>
        <thead>
          <tr>
            <th>Naam</th>
            <th class="num">Aanstellingen</th>
          </tr>
        </thead>
        <tbody>
          {#each hits as row}
            <tr>
              <td>
                <a href="/functies/{row.id}">{String(row.naam)}</a>
              </td>
              <td class="num">{String(row.aanstelling_count ?? '')}</td>
            </tr>
          {/each}
        </tbody>
      </table>
      <Pagination {total} {offset} onpage={(o) => { offset = o; runSearch(); }} />
    </div>
  {/if}
</section>

<style>
  .basic {
    display: flex;
    gap: 0.75rem;
    align-items: flex-end;
    flex-wrap: wrap;
    margin-bottom: 0.75rem;
    padding: 1rem;
    background: var(--raa-surface);
    border: 1px solid var(--raa-line);
    border-radius: var(--raa-radius);
    box-shadow: var(--raa-shadow);
  }
  .q {
    flex: 1;
    min-width: 14rem;
  }
  .az-hint {
    margin: 0.35rem 0 0;
  }
  .results-panel {
    margin-top: 0.75rem;
  }
  .num {
    text-align: right;
    font-variant-numeric: tabular-nums;
    width: 8rem;
  }
</style>
