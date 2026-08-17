<script lang="ts">
  import ActiveChips from '$lib/components/ActiveChips.svelte';
  import AzBrowser from '$lib/components/AzBrowser.svelte';
  import ChipSuggest from '$lib/components/ChipSuggest.svelte';
  import Drawer from '$lib/components/Drawer.svelte';
  import FacetPanel from '$lib/components/FacetPanel.svelte';
  import Pagination from '$lib/components/Pagination.svelte';
  import PersoonHoverPreview from '$lib/components/PersoonHoverPreview.svelte';
  import PersoonPreviewIcon from '$lib/components/PersoonPreviewIcon.svelte';
  import SortPills from '$lib/components/SortPills.svelte';
  import StandAdel from '$lib/components/StandAdel.svelte';
  import { MAX_CHIPS, PAGE_SIZE, periodKey, type FacetValue, type SuggestItem } from '$lib/period';
  import { lifeCell, listingName, searchEntity } from '$lib/search';
  import { HoverPreviewController, createPersoonPreviewHandlers } from '$lib/hoverPreview';
  import { SearchRunGuard } from '$lib/searchRunner';

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
  let refineOpen = $state(false);
  let hoverPersonId = $state<number | null>(null);
  let hoverTop = $state(0);

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
    const token = searchGuard.begin();
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
      if (!searchGuard.isCurrent(token)) return;
      total = data.total;
      hits = data.hits;
      facets = data.facets ?? {};
      hasSearched = true;
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

  function hideHover() {
    preview.hideNow();
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

  $effect(() => {
    if (refineOpen) hideHover();
  });
</script>

<svelte:window
  onscroll={() => hideHover()}
  onresize={() => hideHover()}
/>

<section class="search-page">
  <h2>Personen zoeken</h2>

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
        <input bind:value={q} placeholder="bijv. aylva" />
      </label>
      <button type="submit" disabled={loading}>{loading ? 'Zoeken…' : 'Zoeken'}</button>
      <AzBrowser
        entity="personen"
        compact
        bind:letter
        onchange={() => {
          q = '';
          offset = 0;
          runSearch();
        }}
      />
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
    <p class="err">{error} — start API with <code>./scripts/dev.sh</code></p>
  {/if}

  <ActiveChips chips={activeChips} onClearAll={activeChips.length ? clearFilters : undefined} />

  {#if hasSearched && total !== null}
    <div class="search-results">
      <div class="results-meta">
        <p class="count">{total} treffers</p>
        <SortPills
          bind:sort
          bind:sortDir
          options={[
            ['geslachtsnaam', 'Naam'],
            ['geboortedatum', 'Geboren'],
            ['overlijdensdatum', 'Overleden'],
          ]}
          onchange={() => {
            offset = 0;
            runSearch();
          }}
        />
        <Pagination {total} {offset} onpage={(o) => { offset = o; runSearch(); }} />
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
            {@const id = Number(row.id)}
            <tr>
              <td class="name-cell">
                <a href="/personen/{row.id}">{listingName(row)}</a>
                <PersoonPreviewIcon
                  ontrigger={(e) => preview.showPreview(e, id)}
                  onrelease={preview.hidePreviewSoon}
                  onclick={(e) => preview.togglePreview(e, id)}
                />
              </td>
              <td class="date">
                <span
                  class:estimated={geb.estimated}
                  title={geb.estimated ? 'Geschat uit aanstellingen' : undefined}>{geb.text}</span
                >
              </td>
              <td class="date">
                <span
                  class:estimated={ovl.estimated}
                  title={ovl.estimated ? 'Geschat uit aanstellingen' : undefined}>{ovl.text}</span
                >
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
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
      <legend>Geboorte en overlijden</legend>
      <p class="hint">EDTF, bijv. <code>1700/1750</code>, <code>../1800</code></p>
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
