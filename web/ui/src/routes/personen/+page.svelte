<script lang="ts">
  import ChipSuggest from '$lib/components/ChipSuggest.svelte';
  import FacetPanel from '$lib/components/FacetPanel.svelte';
  import AzBrowser from '$lib/components/AzBrowser.svelte';
  import Pagination from '$lib/components/Pagination.svelte';
  import StandAdel from '$lib/components/StandAdel.svelte';
  import { MAX_CHIPS, PAGE_SIZE, periodKey, type FacetValue, type SuggestItem } from '$lib/period';
  import { lifeCell, listingName, searchEntity } from '$lib/search';

  let q = $state('');
  let letter = $state<string | null>(null);
  let geboorte = $state('');
  let overlijden = $state('');
  let van = $state('');
  let tot = $state('');
  let dateMode = $state<'incl_shadow' | 'exact'>('incl_shadow');
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
  let sort = $state('geslachtsnaam');
  let sortDir = $state<'asc' | 'desc'>('asc');
  let offset = $state(0);
  let advancedOpen = $state(false);

  let total = $state<number | null>(null);
  let hits = $state<Record<string, unknown>[]>([]);
  let facets = $state<Record<string, FacetValue[]>>({});
  let error = $state<string | null>(null);
  let loading = $state(false);
  let hasSearched = $state(false);

  function buildFilters(): Record<string, string[]> {
    const filters: Record<string, string[]> = {};
    if (functies.length) filters.functie_id = functies.map((f) => String(f.id));
    if (instellingen.length) filters.instelling_id = instellingen.map((i) => String(i.id));
    if (provincies.length) filters.provincie_id = provincies.map((p) => String(p.id));
    if (regions.length) filters.regio_id = regions.map((r) => String(r.id));
    if (lokalen.length) filters.lokaal_id = lokalen.map((l) => String(l.id));
    if (standIds.length) filters.stand_id = standIds.map(String);
    if (adelOnly) filters.adel = ['1'];
    if (geboorte.trim()) filters.geboorte = [geboorte.trim()];
    if (overlijden.trim()) filters.overlijden = [overlijden.trim()];
    if (van.trim()) filters.van = [van.trim()];
    if (tot.trim()) filters.tot = [tot.trim()];
    if (letter) filters.letter = [letter];
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
    if (dimension === 'period') {
      periodKey.set(value.key);
      offset = 0;
      return;
    }
    if (dimension === 'adel') {
      adelOnly = !adelOnly;
    } else if (dimension === 'stand') {
      const id = Number(value.key);
      if (standIds.includes(id)) {
        standIds = standIds.filter((x) => x !== id);
      } else {
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
      const data = await searchEntity('personen', {
        q: q.trim() || null,
        filters: buildFilters(),
        functie_match: functieMatch,
        instelling_match: instellingMatch,
        include_shadow_dates: dateMode !== 'exact',
        from: offset,
        size: PAGE_SIZE,
        sort,
        sort_dir: sortDir,
      });
      total = data.total;
      hits = data.hits;
      facets = data.facets ?? {};
      hasSearched = true;
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
    letter = null;
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
    geboorte = '';
    overlijden = '';
    van = '';
    tot = '';
    offset = 0;
    runSearch();
  }

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
    for (const [list, prefix] of [
      [provincies, 'p'],
      [regions, 'r'],
      [lokalen, 'l'],
    ] as const) {
      for (const item of list) {
        chips.push({
          key: `${prefix}-${item.id}`,
          label: item.naam,
          clear: () => {
            if (prefix === 'p') provincies = provincies.filter((x) => x.id !== item.id);
            else if (prefix === 'r') regions = regions.filter((x) => x.id !== item.id);
            else lokalen = lokalen.filter((x) => x.id !== item.id);
            offset = 0;
            runSearch();
          },
        });
      }
    }
    return chips;
  });

  $effect(() => {
    void $periodKey;
    offset = 0;
    runSearch();
  });
</script>

<section>
  <h2>Personen zoeken</h2>

  <form
    class="basic"
    onsubmit={(e) => {
      e.preventDefault();
      submit();
    }}
  >
    <label class="q">
      Naam (wildcards * ?)
      <input bind:value={q} placeholder="bijv. aylva" />
    </label>
    <button type="submit" disabled={loading}>{loading ? 'Zoeken…' : 'Zoeken'}</button>
  </form>

  <p class="hint az-hint">Of blader op geslachtsnaam (A–Z, periode-scoped):</p>
  <AzBrowser
    entity="personen"
    bind:letter
    onchange={() => {
      q = '';
      offset = 0;
      runSearch();
    }}
  />

  <details class="advanced" bind:open={advancedOpen}>
    <summary>Meer filters (datums, typeahead, en/of)</summary>
    <div class="advanced-body">
      <fieldset class="box">
        <legend>Geboorte en overlijden</legend>
        <p class="hint">EDTF, bijv. <code>1700/1750</code>, <code>../1800</code>, <code>1720~</code></p>
        <div class="grid2">
          <label>Geboorte <input bind:value={geboorte} placeholder="1700/1750" /></label>
          <label>Overlijden <input bind:value={overlijden} placeholder="../1800" /></label>
        </div>
        <div class="radios">
          <label><input type="radio" bind:group={dateMode} value="incl_shadow" /> incl. geschatte jaartallen</label>
          <label><input type="radio" bind:group={dateMode} value="exact" /> zoek exacte datums</label>
        </div>
      </fieldset>

      <fieldset class="box">
        <legend>Aanstellingsdatum</legend>
        <p class="hint">Jaar of YYYY-MM-DD</p>
        <div class="grid2">
          <label>Van <input bind:value={van} placeholder="1750" /></label>
          <label>Tot <input bind:value={tot} placeholder="1770" /></label>
        </div>
      </fieldset>

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

      <fieldset class="box">
        <legend>Vertegenwoordiging</legend>
        <div class="grid3">
          <ChipSuggest label="Provinciaal" field="provincie" bind:selected={provincies} showMatch={false} />
          <ChipSuggest label="Regionaal" field="regio" bind:selected={regions} showMatch={false} />
          <ChipSuggest label="Lokaal" field="lokaal" bind:selected={lokalen} showMatch={false} />
        </div>
      </fieldset>

      <StandAdel bind:standIds bind:adelOnly />

      <button type="button" onclick={submit} disabled={loading}>Filters toepassen</button>
    </div>
  </details>

  {#if error}
    <p class="err">{error} — start API with <code>./scripts/dev.sh</code></p>
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

  {#if hasSearched && total !== null}
    <div class="layout">
      <div class="results">
        <p class="count">{total} treffers</p>
        <Pagination {total} {offset} onpage={(o) => { offset = o; runSearch(); }} />
        <div class="sort" aria-label="Sorteer">
          <span class="sort-label">Sorteer:</span>
          {#each [['geslachtsnaam', 'Naam'], ['geboortedatum', 'Geboren'], ['overlijdensdatum', 'Overleden']] as [key, label]}
            <button
              type="button"
              class:active={sort === key}
              class:desc={sort === key && sortDir === 'desc'}
              class:asc={sort === key && sortDir === 'asc'}
              title={sort === key ? (sortDir === 'asc' ? 'Oplopend — klik voor aflopend' : 'Aflopend — klik voor oplopend') : 'Sorteer oplopend'}
              onclick={() => {
                if (sort === key) {
                  sortDir = sortDir === 'asc' ? 'desc' : 'asc';
                } else {
                  sort = key;
                  sortDir = 'asc';
                }
                offset = 0;
                runSearch();
              }}
              >{label}{sort === key ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''}</button
            >
          {/each}
        </div>
        <table>
          <thead>
            <tr>
              <th>Naam</th>
              <th class="date">Geboren</th>
              <th class="date">Overleden</th>
            </tr>
          </thead>
          <tbody>
            {#each hits as row}
              {@const geb = lifeCell(row, 'geboorte')}
              {@const ovl = lifeCell(row, 'overlijden')}
              <tr>
                <td>
                  <a href="/personen/{row.id}">{listingName(row)}</a>
                </td>
                <td class="date">
                  <span class:estimated={geb.estimated} title={geb.estimated ? 'Geschat uit aanstellingen' : undefined}
                    >{geb.text}</span
                  >
                </td>
                <td class="date">
                  <span class:estimated={ovl.estimated} title={ovl.estimated ? 'Geschat uit aanstellingen' : undefined}
                    >{ovl.text}</span
                  >
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
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
  .q input {
    font-size: 1.05rem;
    padding: 0.7rem 0.85rem;
  }
  .az-hint {
    margin: 0.35rem 0 0;
  }
  .sort-label {
    font-size: 0.8rem;
    color: var(--raa-ink-muted);
    margin-right: 0.15rem;
  }
  /* Active sort: ↑ sits above a baseline, ↓ hangs below it */
  .sort button.asc {
    box-shadow: inset 0 2px 0 0 var(--raa-accent-bright);
    padding-top: 0.15rem;
    padding-bottom: 0.35rem;
  }
  .sort button.desc {
    box-shadow: inset 0 -2px 0 0 var(--raa-accent-bright);
    padding-top: 0.35rem;
    padding-bottom: 0.15rem;
  }
  :global(span.estimated),
  .estimated {
    color: var(--raa-ink-faint);
  }
  :global(th.date),
  :global(td.date),
  .date {
    text-align: right;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
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
  .advanced summary:hover {
    color: var(--raa-accent);
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
  .results {
    min-width: 0;
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
    font-weight: 500;
  }
  .active .clear-all {
    background: transparent;
    border: 0;
  }
  .active .clear-all button {
    border: 0;
    background: transparent;
    color: var(--raa-ink-muted);
    text-decoration: underline;
    text-underline-offset: 0.15em;
    padding: 0.2rem 0.35rem;
    font-size: 0.82rem;
  }
  .x {
    border: 0;
    background: transparent;
    cursor: pointer;
    margin-left: 0.15rem;
    color: var(--raa-ink-muted);
  }
  @media (max-width: 800px) {
    .layout {
      grid-template-columns: 1fr;
    }
  }
</style>
