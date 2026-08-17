<script lang="ts">
  import { page } from '$app/stores';
  import ChipSuggest from '$lib/components/ChipSuggest.svelte';
  import FacetPanel from '$lib/components/FacetPanel.svelte';
  import Pagination from '$lib/components/Pagination.svelte';
  import StandAdel from '$lib/components/StandAdel.svelte';
  import { MAX_CHIPS, PAGE_SIZE, periodKey, type FacetValue, type SuggestItem } from '$lib/period';
  import { groupNested, personName, searchEntity } from '$lib/search';
  import { fetchFunctie, fetchInstelling } from '$lib/detail';

  let q = $state('');
  let van = $state('');
  let tot = $state('');
  let groupBy = $state<'instelling' | 'functie'>('instelling');
  let sort = $state('instelling');
  let functies = $state<SuggestItem[]>([]);
  let instellingen = $state<SuggestItem[]>([]);
  let provincies = $state<SuggestItem[]>([]);
  let regions = $state<SuggestItem[]>([]);
  let lokalen = $state<SuggestItem[]>([]);
  let functieMatch = $state<'any' | 'all'>('any');
  let instellingMatch = $state<'any' | 'all'>('any');
  let standIds = $state<number[]>([]);
  let standLabels = $state<Record<number, string>>({});
  let adelOnly = $state(false);
  let offset = $state(0);
  let advancedOpen = $state(false);
  let seeded = $state(false);

  let total = $state<number | null>(null);
  let hits = $state<Record<string, unknown>[]>([]);
  let facets = $state<Record<string, FacetValue[]>>({});
  let error = $state<string | null>(null);
  let loading = $state(false);

  function buildFilters(): Record<string, string[]> {
    const filters: Record<string, string[]> = {};
    if (functies.length) filters.functie_id = functies.map((f) => String(f.id));
    if (instellingen.length) filters.instelling_id = instellingen.map((i) => String(i.id));
    if (provincies.length) filters.provincie_id = provincies.map((p) => String(p.id));
    if (regions.length) filters.regio_id = regions.map((r) => String(r.id));
    if (lokalen.length) filters.lokaal_id = lokalen.map((l) => String(l.id));
    if (standIds.length) filters.stand_id = standIds.map(String);
    if (adelOnly) filters.adel = ['1'];
    if (van.trim()) filters.van = [van.trim()];
    if (tot.trim()) filters.tot = [tot.trim()];
    return filters;
  }

  function selectedFacetKeys(): Record<string, string[]> {
    return {
      adel: adelOnly ? ['1'] : [],
      stand: standIds.map(String),
      functie: functies.map((f) => String(f.id)),
      instelling: instellingen.map((i) => String(i.id)),
      provincie: provincies.map((p) => String(p.id)),
      regio: regions.map((r) => String(r.id)),
      lokaal: lokalen.map((l) => String(l.id)),
    };
  }

  function toggleSuggest(list: SuggestItem[], item: SuggestItem): SuggestItem[] {
    if (list.some((x) => x.id === item.id)) {
      return list.filter((x) => x.id !== item.id);
    }
    if (list.length >= MAX_CHIPS) return list;
    return [...list, item];
  }

  function onFacetToggle(dimension: string, value: FacetValue) {
    if (dimension === 'adel') {
      adelOnly = !adelOnly;
    } else if (dimension === 'stand') {
      const id = Number(value.key);
      if (standIds.includes(id)) standIds = standIds.filter((x) => x !== id);
      else {
        standIds = [...standIds, id];
        standLabels = { ...standLabels, [id]: value.label };
      }
    } else {
      const item = { id: Number(value.key), naam: value.label };
      if (dimension === 'functie') functies = toggleSuggest(functies, item);
      else if (dimension === 'instelling') instellingen = toggleSuggest(instellingen, item);
      else if (dimension === 'provincie') provincies = toggleSuggest(provincies, item);
      else if (dimension === 'regio') regions = toggleSuggest(regions, item);
      else if (dimension === 'lokaal') lokalen = toggleSuggest(lokalen, item);
    }
    offset = 0;
    runSearch();
  }

  async function runSearch() {
    loading = true;
    error = null;
    try {
      const data = await searchEntity('aanstellingen', {
        q: q.trim() || null,
        filters: buildFilters(),
        functie_match: functieMatch,
        instelling_match: instellingMatch,
        from: offset,
        size: PAGE_SIZE,
        sort,
        group_by: null,
      });
      total = data.total;
      hits = data.hits;
      facets = data.facets ?? {};
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
      total = null;
      hits = [];
      facets = {};
    } finally {
      loading = false;
    }
  }

  function submit() {
    offset = 0;
    runSearch();
  }

  function clearFilters() {
    functies = [];
    instellingen = [];
    provincies = [];
    regions = [];
    lokalen = [];
    standIds = [];
    adelOnly = false;
    van = '';
    tot = '';
    offset = 0;
    runSearch();
  }

  const nested = $derived(
    groupNested(
      hits,
      groupBy === 'functie' ? 'functie' : 'instelling',
      groupBy === 'functie' ? 'instelling' : 'functie'
    )
  );

  const activeChips = $derived.by(() => {
    const chips: { key: string; label: string; clear: () => void }[] = [];
    if (adelOnly) {
      chips.push({
        key: 'adel',
        label: 'Adel',
        clear: () => {
          adelOnly = false;
          offset = 0;
          runSearch();
        },
      });
    }
    for (const id of standIds) {
      chips.push({
        key: `stand-${id}`,
        label: standLabels[id] ?? `Stand ${id}`,
        clear: () => {
          standIds = standIds.filter((x) => x !== id);
          offset = 0;
          runSearch();
        },
      });
    }
    for (const item of functies) {
      chips.push({
        key: `f-${item.id}`,
        label: item.naam,
        clear: () => {
          functies = functies.filter((x) => x.id !== item.id);
          offset = 0;
          runSearch();
        },
      });
    }
    for (const item of instellingen) {
      chips.push({
        key: `i-${item.id}`,
        label: item.naam,
        clear: () => {
          instellingen = instellingen.filter((x) => x.id !== item.id);
          offset = 0;
          runSearch();
        },
      });
    }
    return chips;
  });

  async function seedFromQuery() {
    if (seeded) return;
    seeded = true;
    const fid = $page.url.searchParams.get('functie_id');
    const iid = $page.url.searchParams.get('instelling_id');
    if (fid) {
      const id = Number(fid);
      if (!Number.isNaN(id)) {
        try {
          const d = await fetchFunctie(id);
          functies = [{ id, naam: d.naam }];
        } catch {
          functies = [{ id, naam: `functie ${id}` }];
        }
      }
    }
    if (iid) {
      const id = Number(iid);
      if (!Number.isNaN(id)) {
        try {
          const d = await fetchInstelling(id);
          instellingen = [{ id, naam: d.naam }];
        } catch {
          instellingen = [{ id, naam: `instelling ${id}` }];
        }
      }
    }
  }

  $effect(() => {
    void $periodKey;
    void $page.url.search;
    seedFromQuery().finally(() => {
      offset = 0;
      runSearch();
    });
  });
</script>

<section>
  <h2>Aanstellingen zoeken</h2>

  <form
    class="basic"
    onsubmit={(e) => {
      e.preventDefault();
      submit();
    }}
  >
    <label class="q">
      Persoon (optioneel)
      <input bind:value={q} placeholder="naam" />
    </label>
    <button type="submit" disabled={loading}>{loading ? 'Zoeken…' : 'Zoeken'}</button>
  </form>

  <details class="advanced" bind:open={advancedOpen}>
    <summary>Meer filters (datums, typeahead, groepering)</summary>
    <div class="advanced-body">
      <fieldset class="box">
        <legend>Functie en instelling</legend>
        <div class="grid2">
          <ChipSuggest label="Functie" field="functie" bind:selected={functies} bind:match={functieMatch} />
          <ChipSuggest
            label="Instelling"
            field="instelling"
            bind:selected={instellingen}
            bind:match={instellingMatch}
          />
        </div>
      </fieldset>

      <div class="grid2">
        <label>Van (jaar of YYYY-MM-DD) <input bind:value={van} placeholder="1750" /></label>
        <label>Tot (jaar of YYYY-MM-DD) <input bind:value={tot} placeholder="1770" /></label>
      </div>

      <div class="grid2">
        <label>
          Groeperen op
          <select bind:value={groupBy}>
            <option value="instelling">Instelling → functie</option>
            <option value="functie">Functie → instelling</option>
          </select>
        </label>
        <label>
          Sorteren
          <select
            bind:value={sort}
            onchange={() => {
              offset = 0;
              runSearch();
            }}
          >
            <option value="instelling">Instelling</option>
            <option value="functie">Functie</option>
            <option value="van">Aanstellingsdatum (van)</option>
            <option value="geslachtsnaam">Geslachtsnaam</option>
            <option value="voornaam">Voornaam</option>
          </select>
        </label>
      </div>

      <fieldset class="box">
        <legend>Vertegenwoordiging</legend>
        <div class="grid3">
          <ChipSuggest label="Provinciaal" field="provincie" bind:selected={provincies} showMatch={false} />
          <ChipSuggest label="Regionaal" field="regio" bind:selected={regions} showMatch={false} />
          <ChipSuggest label="Lokaal" field="lokaal" bind:selected={lokalen} showMatch={false} />
        </div>
      </fieldset>

      <StandAdel bind:standIds bind:adelOnly />
      <button type="button" class="primary" onclick={submit} disabled={loading}>Filters toepassen</button>
    </div>
  </details>

  {#if error}
    <p class="err">{error}</p>
  {/if}

  {#if activeChips.length}
    <ul class="active">
      {#each activeChips as chip}
        <li>
          {chip.label}
          <button type="button" class="x" onclick={chip.clear} aria-label="verwijder">×</button>
        </li>
      {/each}
      <li class="clear-all">
        <button type="button" onclick={clearFilters}>Wis filters</button>
      </li>
    </ul>
  {/if}

  {#if total !== null}
    <div class="layout">
      <div class="results">
        <p class="count">{total} treffers</p>
        <Pagination {total} {offset} onpage={(o) => { offset = o; runSearch(); }} />
        {#each nested as outer}
          <section class="outer">
            <h3>
              {#if groupBy === 'instelling' && outer.id}
                <a href="/instellingen/{outer.id}">{outer.naam || '(onbekend)'}</a>
              {:else if groupBy === 'functie' && outer.id}
                <a href="/functies/{outer.id}">{outer.naam || '(onbekend)'}</a>
              {:else}
                {outer.naam || '(onbekend)'}
              {/if}
            </h3>
            {#each outer.inner as inner}
              <div class="inner">
                <h4>
                  {#if groupBy === 'instelling' && inner.id}
                    <a href="/functies/{inner.id}">{inner.naam || '(onbekend)'}</a>
                  {:else if groupBy === 'functie' && inner.id}
                    <a href="/instellingen/{inner.id}">{inner.naam || '(onbekend)'}</a>
                  {:else}
                    {inner.naam || '(onbekend)'}
                  {/if}
                </h4>
                <ul>
                  {#each inner.rows as row}
                    <li>
                      <a href="/personen/{row.persoon_id}">{personName(row)}</a>
                      <span class="dates"
                        >({String(row.van_als_bekend ?? '?')} – {String(row.tot_als_bekend ?? '?')})</span
                      >
                    </li>
                  {/each}
                </ul>
              </div>
            {/each}
          </section>
        {/each}
        <Pagination {total} {offset} onpage={(o) => { offset = o; runSearch(); }} />
      </div>
      <FacetPanel facets={facets} selectedKeys={selectedFacetKeys()} ontoggle={onFacetToggle} />
    </div>
  {/if}
</section>

<style>
  .basic {
    display: flex;
    gap: 0.75rem;
    align-items: flex-end;
    flex-wrap: wrap;
    margin-bottom: 1rem;
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
  .advanced {
    margin-bottom: 1rem;
    border: 1px solid var(--raa-line);
    background: var(--raa-surface);
    padding: 0.35rem 0.85rem 0.85rem;
    border-radius: var(--raa-radius);
  }
  .advanced summary {
    cursor: pointer;
    font-weight: 600;
    font-size: 0.9rem;
    padding: 0.55rem 0;
    color: var(--raa-ink-muted);
  }
  .advanced-body {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-top: 0.35rem;
    padding-top: 0.35rem;
    border-top: 1px solid var(--raa-line);
  }
  .layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 16rem;
    gap: 1.5rem;
    align-items: start;
  }
  .active {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    list-style: none;
    margin: 0 0 1rem;
    padding: 0;
  }
  .active li {
    background: var(--raa-accent-soft);
    border: 1px solid var(--raa-chip-border);
    border-radius: 999px;
    padding: 0.2rem 0.55rem;
    font-size: 0.82rem;
  }
  .active .clear-all {
    background: transparent;
    border: 0;
  }
  .x {
    border: 0;
    background: transparent;
    cursor: pointer;
  }
  .outer {
    margin: 1.1rem 0;
    background: var(--raa-surface);
    border: 1px solid var(--raa-line);
    border-radius: var(--raa-radius);
    padding: 0.85rem 1rem;
  }
  .outer h3 {
    margin: 0 0 0.5rem;
    padding-bottom: 0.4rem;
    border-bottom: 2px solid var(--raa-accent-bright);
    font-size: 1.05rem;
  }
  .outer h3 a {
    text-decoration: none;
  }
  .inner {
    margin: 0.65rem 0 0.35rem;
  }
  .inner h4 {
    margin: 0 0 0.3rem;
    font-size: 0.9rem;
    color: var(--raa-ink-muted);
  }
  .inner h4 a {
    color: inherit;
    text-decoration: none;
  }
  .inner h4 a:hover {
    color: var(--raa-accent);
  }
  ul {
    margin: 0;
    padding-left: 1.1rem;
  }
  .dates {
    color: var(--raa-ink-faint);
    font-variant-numeric: tabular-nums;
  }
  @media (max-width: 800px) {
    .layout {
      grid-template-columns: 1fr;
    }
  }
</style>
