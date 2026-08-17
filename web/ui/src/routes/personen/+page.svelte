<script lang="ts">
  import { goto, replaceState } from '$app/navigation';
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import ActiveChips from '$lib/components/ActiveChips.svelte';
  import AzBrowser from '$lib/components/AzBrowser.svelte';
  import ChipSuggest from '$lib/components/ChipSuggest.svelte';
  import Drawer from '$lib/components/Drawer.svelte';
  import FacetPanel from '$lib/components/FacetPanel.svelte';
  import SummaryPanel from '$lib/components/SummaryPanel.svelte';
  import Pagination from '$lib/components/Pagination.svelte';
  import PersoonHoverPreview from '$lib/components/PersoonHoverPreview.svelte';
  import PersoonPreviewIcon from '$lib/components/PersoonPreviewIcon.svelte';
  import SortPills from '$lib/components/SortPills.svelte';
  import StandAdel from '$lib/components/StandAdel.svelte';
  import YearHistogram from '$lib/components/YearHistogram.svelte';
  import { MAX_CHIPS, pageSize, periodKey, periodMode, type FacetValue, type SuggestItem } from '$lib/period';
  import { lifeCell, listingName, loadStands, searchEntity } from '$lib/search';
  import {
    geboorteEdtfRange,
    timelineChartTitle,
    timelineFilterYears,
    type TimelineBin,
    type TimelineMeta,
    type YearCount,
  } from '$lib/yearHistogram';
  import { HoverPreviewController, createPersoonPreviewHandlers } from '$lib/hoverPreview';
  import { SearchRunGuard } from '$lib/searchRunner';
  import { fetchFunctie, fetchInstelling } from '$lib/detail';
  import {
    applyPeriodFromParams,
    parsePersonenParams,
    parseAanstellingenParams,
    resolveSuggestItems,
    edtfRangeChipLabel,
    aanstellingDateChipLabel,
    EMPTY_NAME_PARTS,
    namePartChipLabel,
    personenFilters,
    personenListPath,
    type NameSearchMode,
    type PersonenNameParts,
    type PersonenSearchState,
  } from '$lib/searchUrl';
  import { patchOverviewPersonen, saveOverviewSnapshot } from '$lib/overviewStore';

  const searchGuard = new SearchRunGuard();
  const hoverCtl = new HoverPreviewController();
  const preview = createPersoonPreviewHandlers({
    hoverCtl,
    isBlocked: () => refineOpen || summaryOpen || naamOpen,
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
  let qMode = $state<NameSearchMode>('prefix');
  let nameParts = $state<PersonenNameParts>({ ...EMPTY_NAME_PARTS });
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
  let naamOpen = $state(false);
  let summaryOpen = $state(false);
  let hoverPersonId = $state<number | null>(null);
  let hoverTop = $state(0);

  let total = $state<number | null>(null);
  let hits = $state<Record<string, unknown>[]>([]);
  let facets = $state<Record<string, FacetValue[]>>({});
  let timeline = $state<YearCount[]>([]);
  let timelineMeta = $state<TimelineMeta | null>(null);
  let error = $state<string | null>(null);
  let loading = $state(false);
  let hasSearched = $state(false);

  function personenUrlState(): PersonenSearchState {
    return {
      q,
      qMode,
      nameParts,
      letter,
      geboorte,
      overlijden,
      van,
      tot,
      dateMode,
      functieIds: functies.map((f) => f.id),
      instellingIds: instellingen.map((i) => i.id),
      provincieIds: provincies.map((p) => p.id),
      regioIds: regions.map((r) => r.id),
      lokalIds: lokalen.map((l) => l.id),
      standIds,
      adel: adelOnly,
      functieMatch,
      instellingMatch,
    };
  }

  async function seedFromUrl() {
    const params = $page.url.searchParams;
    if (!params.toString()) return;
    const parsed = parsePersonenParams(params);
    const period = applyPeriodFromParams(params);
    if (period && period !== get(periodKey)) periodKey.set(period);
    q = parsed.q;
    qMode = parsed.qMode;
    nameParts = { ...parsed.nameParts };
    letter = parsed.letter;
    geboorte = parsed.geboorte;
    overlijden = parsed.overlijden;
    van = parsed.van;
    tot = parsed.tot;
    dateMode = parsed.dateMode;
    adelOnly = parsed.adel;
    functieMatch = parsed.functieMatch;
    instellingMatch = parsed.instellingMatch;
    standIds = parsed.standIds;
    const [functieItems, instellingItems, stands] = await Promise.all([
      resolveSuggestItems(fetchFunctie, parsed.functieIds),
      resolveSuggestItems(fetchInstelling, parsed.instellingIds),
      loadStands(),
    ]);
    functies = functieItems;
    instellingen = instellingItems;
    for (const stand of stands) {
      if (parsed.standIds.includes(stand.id)) {
        standLabels = { ...standLabels, [stand.id]: stand.naam };
      }
    }
  }

  function openOverview() {
    if (total === null) return;
    saveOverviewSnapshot({
      entity: 'personen',
      period: get(periodKey),
      personen: personenUrlState(),
      total,
      facets,
      timeline,
      timelineMeta,
    });
    goto('/personen/overzicht');
  }

  function buildFilters(): Record<string, string[]> {
    return personenFilters(personenUrlState());
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

  function commitListState() {
    const period = get(periodKey);
    const state = personenUrlState();
    replaceState(personenListPath(state, period), {});
    patchOverviewPersonen(state, period);
  }

  async function runSearch() {
    const token = searchGuard.begin();
    loading = true;
    error = null;
    try {
      const data = await searchEntity('personen', {
        q: q.trim() || null,
        q_mode: qMode,
        filters: buildFilters(),
        functie_match: functieMatch,
        instelling_match: instellingMatch,
        include_shadow_dates: dateMode !== 'exact',
        from: offset,
        size: get(pageSize),
        sort,
        sort_dir: sortDir,
      });
      if (!searchGuard.isCurrent(token)) return;
      total = data.total;
      hits = data.hits;
      facets = data.facets ?? {};
      timeline = data.timeline ?? [];
      timelineMeta = data.timeline_meta ?? null;
      hasSearched = true;
      commitListState();
    } catch (e) {
      if (!searchGuard.isCurrent(token)) return;
      error = e instanceof Error ? e.message : String(e);
      total = null;
      hits = [];
      facets = {};
      timeline = [];
      timelineMeta = null;
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

  function onTimelineSelect(year: number, period?: string) {
    if (!timelineMeta) return;
    const { from, to } = timelineFilterYears(year, timelineMeta.bin as TimelineBin);
    geboorte = geboorteEdtfRange(from, to);
    offset = 0;
    if (period && period !== get(periodKey)) {
      periodKey.set(period);
    } else {
      runSearch();
    }
  }

  const includeShadowDates = $derived(dateMode !== 'exact');
  const timelineTitle = $derived(timelineChartTitle('personen', includeShadowDates));

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
    nameParts = { ...EMPTY_NAME_PARTS };
    offset = 0;
    runSearch();
  }

  function hideHover() {
    preview.hideNow();
  }

  function applyNameParts() {
    offset = 0;
    naamOpen = false;
    runSearch();
  }

  const qModeHint = $derived(
    qMode === 'prefix'
      ? 'Begint met — bijv. aylva'
      : qMode === 'contains'
        ? 'Bevat — substring in naamvelden'
        : qMode === 'exact'
          ? 'Exact — hele veldwaarde (hoofdletterongevoelig)'
          : 'Patroon — wildcards * en ?'
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
    if (geboorte.trim()) {
      chips.push({
        key: 'geboorte',
        label: edtfRangeChipLabel('Geboorte', geboorte),
        clear: () => {
          geboorte = '';
          offset = 0;
          runSearch();
        },
      });
    }
    for (const key of Object.keys(nameParts) as (keyof PersonenNameParts)[]) {
      const value = nameParts[key].trim();
      if (!value) continue;
      chips.push({
        key: `name-${key}`,
        label: namePartChipLabel(key, value),
        clear: () => {
          nameParts = { ...nameParts, [key]: '' };
          offset = 0;
          runSearch();
        },
      });
    }
    if (overlijden.trim()) {
      chips.push({
        key: 'overlijden',
        label: edtfRangeChipLabel('Overlijden', overlijden),
        clear: () => {
          overlijden = '';
          offset = 0;
          runSearch();
        },
      });
    }
    const aanstLabel = aanstellingDateChipLabel(van, tot);
    if (aanstLabel) {
      chips.push({
        key: 'aanstelling-dates',
        label: aanstLabel,
        clear: () => {
          van = '';
          tot = '';
          offset = 0;
          runSearch();
        },
      });
    }
    return chips;
  });

  onMount(() => {
    let searchReady = false;
    let lastPeriod = get(periodKey);

    void (async () => {
      await seedFromUrl();
      lastPeriod = get(periodKey);
      offset = 0;
      await runSearch();
      searchReady = true;
    })();

    const unsub = periodKey.subscribe((p) => {
      if (!searchReady || p === lastPeriod) return;
      lastPeriod = p;
      offset = 0;
      runSearch();
    });

    return unsub;
  });

  $effect(() => {
    if (refineOpen || summaryOpen || naamOpen) hideHover();
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
        <span class="q-label-row">
          <span>Naam</span>
          <select class="q-mode" bind:value={qMode} aria-label="Naam zoekmodus">
            <option value="prefix">Begint met</option>
            <option value="contains">Bevat</option>
            <option value="pattern">Patroon (* ?)</option>
            <option value="exact">Exact</option>
          </select>
        </span>
        <input bind:value={q} placeholder={qModeHint} />
      </label>
      <button type="submit" disabled={loading}>{loading ? 'Zoeken…' : 'Zoeken'}</button>
      <button
        type="button"
        class="btn-ghost"
        class:active={naamOpen}
        onclick={() => (naamOpen = !naamOpen)}
      >
        Naam onderdelen ▾
      </button>
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
      class:active={summaryOpen}
      disabled={!hasSearched}
      onclick={() => (summaryOpen = !summaryOpen)}
    >
      Samenvatting
    </button>
    {#if hasSearched}
      <button type="button" class="btn-ghost" onclick={openOverview}>Overzicht →</button>
    {/if}
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
        <Pagination
          {total}
          {offset}
          pageSize={$pageSize}
          onpage={onPageChange}
          {onPageSizeChange}
        />
      </div>
      {#if timeline.length > 0 && timelineMeta}
        <YearHistogram
          compact
          title={timelineTitle}
          bins={timeline}
          bin={timelineMeta.bin}
          stacked={timelineMeta.stacked ?? false}
          entity="personen"
          includeShadowDates={includeShadowDates}
          undated={timelineMeta.undated}
          onselect={onTimelineSelect}
        />
      {/if}
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
                <div class="name-cell-inner">
                  <a href="/personen/{row.id}">{listingName(row)}</a>
                  <PersoonPreviewIcon
                    ontrigger={(e) => preview.showPreview(e, id)}
                    onrelease={preview.hidePreviewSoon}
                    onclick={(e) => preview.togglePreview(e, id)}
                  />
                </div>
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
                  title={ovl.estimated ? 'Overlijden onbekend; na laatste aanstelling' : undefined}>{ovl.text}</span
                >
              </td>
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

<Drawer bind:open={naamOpen} title="Naam onderdelen">
  <p class="hint name-parts-hint">
    Zoek per veld (wildcards <code>*</code> <code>?</code> toegestaan). Ingevulde velden worden gecombineerd met <strong>en</strong>.
  </p>
  <div class="name-parts-grid">
    <label>Geslachtsnaam <input bind:value={nameParts.geslachtsnaam} placeholder="bijv. Aylva" /></label>
    <label>Voornaam <input bind:value={nameParts.voornaam} placeholder="bijv. Tjaerd" /></label>
    <label>Tussenvoegsel <input bind:value={nameParts.tussenvoegsel} placeholder="bijv. van" /></label>
    <label>Naamsvariant <input bind:value={nameParts.alias} placeholder="alias" /></label>
    <label>Heerlijkheid <input bind:value={nameParts.heerlijkheid} placeholder="bijv. Oldeboorn" /></label>
  </div>
  <button type="button" class="primary" onclick={applyNameParts} disabled={loading}>Zoeken</button>
</Drawer>

<SummaryPanel
  bind:open={summaryOpen}
  entity="personen"
  facets={facets}
  periodMode={$periodMode}
  {hasSearched}
  {total}
  {timeline}
  {timelineMeta}
  includeShadowDates={includeShadowDates}
  onselect={onFacetToggle}
  {onTimelineSelect}
/>

<PersoonHoverPreview
  open={hoverPersonId != null}
  personId={hoverPersonId}
  anchorTop={hoverTop}
  onenter={() => hoverCtl.cancel()}
  onleave={preview.hidePreviewSoon}
/>
