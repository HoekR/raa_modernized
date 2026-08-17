<script lang="ts">
  import AzBrowser from '$lib/components/AzBrowser.svelte';
  import Pagination from '$lib/components/Pagination.svelte';
  import { get } from 'svelte/store';
  import { pageSize, periodKey } from '$lib/period';
  import { browseAz, searchEntity } from '$lib/search';
  import { SearchRunGuard } from '$lib/searchRunner';

  const searchGuard = new SearchRunGuard();

  let q = $state('');
  let letter = $state<string | null>(null);
  let offset = $state(0);
  let total = $state<number | null>(null);
  let hits = $state<Record<string, unknown>[]>([]);
  let error = $state<string | null>(null);
  let loading = $state(false);

  async function runSearch() {
    const token = searchGuard.begin();
    loading = true;
    error = null;
    try {
      let data;
      if (letter && !q.trim()) {
        data = await browseAz('functies', { letter, from: offset, size: get(pageSize) });
      } else {
        data = await searchEntity('functies', {
          q: q.trim() || null,
          from: offset,
          size: get(pageSize),
        });
      }
      if (!searchGuard.isCurrent(token)) return;
      total = data.total;
      hits = data.hits;
    } catch (e) {
      if (!searchGuard.isCurrent(token)) return;
      error = e instanceof Error ? e.message : String(e);
      total = null;
      hits = [];
    } finally {
      if (searchGuard.isCurrent(token)) loading = false;
    }
  }

  function submit() {
    letter = null;
    offset = 0;
    runSearch();
  }

  function onPageChange(o: number) {
    offset = o;
    runSearch();
  }

  function onPageSizeChange(n: number) {
    pageSize.set(n);
    offset = 0;
    runSearch();
  }

  $effect(() => {
    void $periodKey;
    offset = 0;
    runSearch();
  });
</script>

<section class="search-page">
  <h2>Functies zoeken</h2>

  <form
    class="search-toolbar"
    onsubmit={(e) => {
      e.preventDefault();
      submit();
    }}
  >
    <div class="search-toolbar-left">
      <label class="q">
        Naam (wildcards * ?)
        <input bind:value={q} placeholder="bijv. burgemeester*" />
      </label>
      <button type="submit" disabled={loading}>{loading ? 'Zoeken…' : 'Zoeken'}</button>
      <AzBrowser
        entity="functies"
        compact
        bind:letter
        onchange={() => {
          q = '';
          offset = 0;
          runSearch();
        }}
      />
    </div>
  </form>

  {#if error}
    <p class="err">{error}</p>
  {/if}

  {#if total !== null}
    <div class="search-results">
      <div class="results-meta">
        <p class="count">{total} treffers</p>
        <Pagination
          {total}
          {offset}
          pageSize={$pageSize}
          onpage={onPageChange}
          {onPageSizeChange}
        />
      </div>
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
      <Pagination
        {total}
        {offset}
        pageSize={$pageSize}
        onpage={onPageChange}
        onPageSizeChange={onPageSizeChange}
      />
    </div>
  {/if}
</section>
