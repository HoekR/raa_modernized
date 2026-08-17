<script lang="ts">
  import { page } from '$app/stores';
  import ActiveChips from '$lib/components/ActiveChips.svelte';
  import ChipSuggest from '$lib/components/ChipSuggest.svelte';
  import Drawer from '$lib/components/Drawer.svelte';
  import FacetPanel from '$lib/components/FacetPanel.svelte';
  import Pagination from '$lib/components/Pagination.svelte';
  import PersoonHoverPreview from '$lib/components/PersoonHoverPreview.svelte';
  import PersoonPreviewIcon from '$lib/components/PersoonPreviewIcon.svelte';
  import StandAdel from '$lib/components/StandAdel.svelte';
  import { MAX_CHIPS, PAGE_SIZE, periodKey, type FacetValue, type SuggestItem } from '$lib/period';
  import { groupNested, personName, searchEntity } from '$lib/search';
  import { fetchFunctie, fetchInstelling } from '$lib/detail';
  import { SearchRunGuard } from '$lib/searchRunner';
  import { HoverPreviewController, createPersoonPreviewHandlers } from '$lib/hoverPreview';

  const searchGuard = new SearchRunGuard();
  const hoverCtl = new HoverPreviewController();
  const preview = createPersoonPreviewHandlers({
    hoverCtl,
    isBlocked: () => refineOpen,
    getActiveId: () => hoverPersonId,
    show: (id, top) => {
      hoverPersonId = id;
      hoverTop = top;
    },
    hide: () => {
      hoverPersonId = null;
    },
  });

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
  let refineOpen = $state(false);
  let hoverPersonId = $state<number | null>(null);
  let hoverTop = $state(0);
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
    const token = searchGuard.begin();
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
      if (!searchGuard.isCurrent(token)) return;
      total = data.total;
      hits = data.hits;
      facets = data.facets ?? {};
    } catch (e) {
      if (!searchGuard.isCurrent(token)) return;
      error = e instanceof Error ? e.message : String(e);
      total = null;
      hits = [];
      facets = {};
    } finally {
      if (searchGuard.isCurrent(token)) loading = false;
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

  function hideHover() {
    preview.hideNow();
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

  $effect(() => {
    if (refineOpen) hideHover();
  });
</script>

<svelte:window
  onscroll={() => hideHover()}
  onresize={() => hideHover()}
/>

<section class="search-page">
  <h2>Aanstellingen zoeken</h2>

  <form
    class="search-toolbar"
    onsubmit={(e) => {
      e.preventDefault();
      submit();
    }}
  >
    <div class="search-toolbar-left">
      <label class="q">
        Persoon (optioneel)
        <input bind:value={q} placeholder="naam" />
      </label>
      <button type="submit" disabled={loading}>{loading ? 'Zoeken…' : 'Zoeken'}</button>
    </div>
    <button
      type="button"
      class="btn-ghost"
      class:active={refineOpen}
      onclick={() => (refineOpen = !refineOpen)}
    >
      Verfijnen ▾
    </button>
  </form>

  {#if error}
    <p class="err">{error}</p>
  {/if}

  <ActiveChips chips={activeChips} onClearAll={activeChips.length ? clearFilters : undefined} />

  {#if total !== null}
    <div class="search-results">
      <div class="results-meta">
        <p class="count">{total} treffers</p>
        <Pagination {total} {offset} onpage={(o) => { offset = o; runSearch(); }} />
      </div>
      {#each nested as outer}
        <section class="nested-group">
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
            <div class="nested-inner">
              <h4>
                {#if groupBy === 'instelling' && inner.id}
                  <a href="/functies/{inner.id}">{inner.naam || '(onbekend)'}</a>
                {:else if groupBy === 'functie' && inner.id}
                  <a href="/instellingen/{inner.id}">{inner.naam || '(onbekend)'}</a>
                {:else}
                  {inner.naam || '(onbekend)'}
                {/if}
              </h4>
              <table>
                <thead>
                  <tr>
                    <th>Persoon</th>
                    <th class="date">Van</th>
                    <th class="date">Tot</th>
                  </tr>
                </thead>
                <tbody>
                  {#each inner.rows as row}
                    {@const pid = Number(row.persoon_id)}
                    <tr>
                      <td class="name-cell">
                        <a href="/personen/{row.persoon_id}">{personName(row)}</a>
                        {#if !Number.isNaN(pid)}
                          <PersoonPreviewIcon
                            ontrigger={(e) => preview.showPreview(e, pid)}
                            onrelease={preview.hidePreviewSoon}
                            onclick={(e) => preview.togglePreview(e, pid)}
                          />
                        {/if}
                      </td>
                      <td class="date">{String(row.van_als_bekend ?? '?')}</td>
                      <td class="date">{String(row.tot_als_bekend ?? '?')}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          {/each}
        </section>
      {/each}
      <Pagination {total} {offset} onpage={(o) => { offset = o; runSearch(); }} />
    </div>
  {/if}
</section>

<Drawer bind:open={refineOpen} title="Verfijnen">
  <FacetPanel
    embedded
    facets={facets}
    selectedKeys={selectedFacetKeys()}
    ontoggle={onFacetToggle}
  />
  <div class="refine-advanced">
    <h4>Meer filters</h4>
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
</Drawer>

<PersoonHoverPreview
  open={hoverPersonId != null}
  personId={hoverPersonId}
  anchorTop={hoverTop}
  onenter={() => hoverCtl.cancel()}
  onleave={preview.hidePreviewSoon}
/>

<style>
  .nested-group {
    margin: 1rem 0;
    background: var(--raa-surface);
    border: 1px solid var(--raa-line);
    border-radius: var(--raa-radius);
    padding: 0.85rem 1rem;
  }
  .nested-group h3 {
    margin: 0 0 0.5rem;
    padding-bottom: 0.4rem;
    border-bottom: 2px solid var(--raa-accent-bright);
    font-size: 1.05rem;
  }
  .nested-group h3 a {
    text-decoration: none;
  }
  .nested-inner {
    margin: 0.65rem 0 0.35rem;
  }
  .nested-inner h4 {
    margin: 0 0 0.35rem;
    font-size: 0.9rem;
    color: var(--raa-ink-muted);
  }
  .nested-inner h4 a {
    color: inherit;
    text-decoration: none;
  }
  .nested-inner h4 a:hover {
    color: var(--raa-accent);
  }
</style>
