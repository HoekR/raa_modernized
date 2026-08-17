<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import FacetSummary from '$lib/components/FacetSummary.svelte';
  import {
    ALL_PERIODS_LABEL,
    type FacetValue,
    periodKey,
    periodMode,
    type SuggestItem,
  } from '$lib/period';
  import {
    loadOverviewSnapshot,
    saveOverviewSnapshot,
    updateOverviewSnapshot,
    type OverviewSnapshot,
  } from '$lib/overviewStore';
  import { searchSummary } from '$lib/search';
  import {
    applyPeriodFromParams,
    listHref,
    parseAanstellingenParams,
    parsePersonenParams,
    sharedFilters,
    toggleId,
    EMPTY_NAME_PARTS,
    namePartChipLabel,
    type AanstellingenSearchState,
    type EntityKind,
    type PersonenSearchState,
    personenFilters,
  } from '$lib/searchUrl';
  import { SearchRunGuard } from '$lib/searchRunner';
  import {
    geboorteEdtfRange,
    timelineFilterYears,
    type TimelineBin,
    type TimelineMeta,
    type YearCount,
  } from '$lib/yearHistogram';

  let {
    entity,
    title,
  }: {
    entity: EntityKind;
    title: string;
  } = $props();

  const searchGuard = new SearchRunGuard();

  let personenState = $state<PersonenSearchState>({
    q: '',
    van: '',
    tot: '',
    functieIds: [],
    instellingIds: [],
    provincieIds: [],
    regioIds: [],
    lokalIds: [],
    standIds: [],
    adel: false,
    functieMatch: 'any',
    instellingMatch: 'any',
    letter: null,
    geboorte: '',
    overlijden: '',
    dateMode: 'incl_shadow',
    qMode: 'prefix',
    nameParts: { ...EMPTY_NAME_PARTS },
  });

  let aanstellingenState = $state<AanstellingenSearchState>({
    q: '',
    van: '',
    tot: '',
    functieIds: [],
    instellingIds: [],
    provincieIds: [],
    regioIds: [],
    lokalIds: [],
    standIds: [],
    adel: false,
    functieMatch: 'any',
    instellingMatch: 'any',
    groupBy: 'instelling',
    sort: 'instelling',
  });

  let functieLabels = $state<SuggestItem[]>([]);
  let instellingLabels = $state<SuggestItem[]>([]);
  let standLabels = $state<Record<number, string>>({});

  let total = $state<number | null>(null);
  let facets = $state<Record<string, FacetValue[]>>({});
  let timeline = $state<YearCount[]>([]);
  let timelineMeta = $state<TimelineMeta | null>(null);
  let error = $state<string | null>(null);
  let loading = $state(false);
  let hasSearched = $state(false);

  let periodUnsub: (() => void) | null = null;
  let trackedPeriod = '';
  let overviewReady = false;

  const includeShadowDates = $derived(
    entity === 'personen' ? personenState.dateMode !== 'exact' : true
  );

  function applySnapshot(snap: OverviewSnapshot) {
    if (snap.period && snap.period !== get(periodKey)) {
      periodKey.set(snap.period);
    }
    trackedPeriod = get(periodKey);
    if (snap.personen) personenState = snap.personen;
    if (snap.aanstellingen) aanstellingenState = snap.aanstellingen;
    total = snap.total;
    facets = snap.facets;
    timeline = snap.timeline;
    timelineMeta = snap.timelineMeta;
    syncLabelCaches();
    hasSearched = true;
  }

  function syncLabelCaches() {
    const shared = entity === 'personen' ? personenState : aanstellingenState;
    functieLabels = shared.functieIds.map((id) => ({
      id,
      naam: facets.functie?.find((f) => f.key === String(id))?.label ?? `#${id}`,
    }));
    instellingLabels = shared.instellingIds.map((id) => ({
      id,
      naam: facets.instelling?.find((f) => f.key === String(id))?.label ?? `#${id}`,
    }));
    const labels: Record<number, string> = {};
    for (const id of shared.standIds) {
      labels[id] = facets.stand?.find((f) => f.key === String(id))?.label ?? String(id);
    }
    standLabels = labels;
  }

  function currentSnapshot(): OverviewSnapshot {
    return {
      entity,
      period: get(periodKey),
      personen: entity === 'personen' ? personenState : undefined,
      aanstellingen: entity === 'aanstellingen' ? aanstellingenState : undefined,
      total: total ?? 0,
      facets,
      timeline,
      timelineMeta,
    };
  }

  async function refreshSearch() {
    const token = searchGuard.begin();
    loading = true;
    error = null;
    try {
      const body =
        entity === 'personen'
          ? {
              q: personenState.q.trim() || null,
              q_mode: personenState.qMode,
              filters: personenFilters(personenState),
              functie_match: personenState.functieMatch,
              instelling_match: personenState.instellingMatch,
              include_shadow_dates: includeShadowDates,
            }
          : {
              q: aanstellingenState.q.trim() || null,
              filters: sharedFilters(aanstellingenState),
              functie_match: aanstellingenState.functieMatch,
              instelling_match: aanstellingenState.instellingMatch,
            };
      const data = await searchSummary(entity, body);
      if (!searchGuard.isCurrent(token)) return;
      total = data.total;
      facets = data.facets ?? {};
      timeline = data.timeline ?? [];
      timelineMeta = data.timeline_meta ?? null;
      hasSearched = true;
      syncLabelCaches();
      saveOverviewSnapshot(currentSnapshot());
    } catch (e) {
      if (!searchGuard.isCurrent(token)) return;
      error = e instanceof Error ? e.message : String(e);
      hasSearched = true;
    } finally {
      if (searchGuard.isCurrent(token)) loading = false;
    }
  }

  function commitFilterChange() {
    void refreshSearch();
  }

  function onFacetToggle(dimension: string, value: FacetValue) {
    if (dimension === 'period') {
      periodKey.set(value.key);
      return;
    }
    if (dimension === 'adel') {
      if (entity === 'personen') personenState = { ...personenState, adel: !personenState.adel };
      else aanstellingenState = { ...aanstellingenState, adel: !aanstellingenState.adel };
    } else if (dimension === 'stand') {
      const id = Number(value.key);
      if (entity === 'personen') {
        personenState = { ...personenState, standIds: toggleId(personenState.standIds, id) };
      } else {
        aanstellingenState = { ...aanstellingenState, standIds: toggleId(aanstellingenState.standIds, id) };
      }
    } else {
      const id = Number(value.key);
      if (dimension === 'functie') {
        const shared = entity === 'personen' ? personenState : aanstellingenState;
        const nextIds = toggleId(shared.functieIds, id);
        if (entity === 'personen') {
          personenState = { ...personenState, functieIds: nextIds };
        } else {
          aanstellingenState = { ...aanstellingenState, functieIds: nextIds };
        }
      } else if (dimension === 'instelling') {
        const shared = entity === 'personen' ? personenState : aanstellingenState;
        const nextIds = toggleId(shared.instellingIds, id);
        if (entity === 'personen') {
          personenState = { ...personenState, instellingIds: nextIds };
        } else {
          aanstellingenState = { ...aanstellingenState, instellingIds: nextIds };
        }
      }
    }
    commitFilterChange();
  }

  function onTimelineSelect(year: number, period?: string) {
    if (!timelineMeta) return;
    const { from, to } = timelineFilterYears(year, timelineMeta.bin as TimelineBin);
    if (entity === 'personen') {
      personenState = {
        ...personenState,
        geboorte: geboorteEdtfRange(from, to),
      };
    } else {
      aanstellingenState = {
        ...aanstellingenState,
        van: String(from),
        tot: String(to),
      };
    }
    if (period) {
      if (period !== get(periodKey)) periodKey.set(period);
      else commitFilterChange();
    } else {
      commitFilterChange();
    }
  }

  const listBackHref = $derived(
    entity === 'personen'
      ? listHref('personen', personenState, $periodKey)
      : listHref('aanstellingen', aanstellingenState, $periodKey)
  );

  const queryLines = $derived.by(() => {
    const lines: string[] = [];
    const shared = entity === 'personen' ? personenState : aanstellingenState;
    if (shared.q.trim()) {
      if (entity === 'personen') lines.push(`Zoekterm: ${shared.q.trim()} (${personenState.qMode})`);
      else lines.push(`Zoekterm: ${shared.q.trim()}`);
    }
    if (entity === 'personen') {
      for (const key of Object.keys(personenState.nameParts) as (keyof typeof personenState.nameParts)[]) {
        const value = personenState.nameParts[key].trim();
        if (value) lines.push(namePartChipLabel(key, value));
      }
    }
    if (entity === 'personen' && personenState.letter) {
      lines.push(`Letter: ${personenState.letter}`);
    }
    if (entity === 'personen' && personenState.geboorte.trim()) {
      lines.push(`Geboorte: ${personenState.geboorte.trim()}`);
    }
    if (entity === 'personen' && personenState.overlijden.trim()) {
      lines.push(`Overlijden: ${personenState.overlijden.trim()}`);
    }
    if (shared.van.trim() || shared.tot.trim()) {
      lines.push(`Aanstelling: ${shared.van.trim() || '…'} – ${shared.tot.trim() || '…'}`);
    }
    for (const item of functieLabels) lines.push(`Functie: ${item.naam}`);
    for (const item of instellingLabels) lines.push(`Instelling: ${item.naam}`);
    for (const id of shared.standIds) lines.push(`Stand: ${standLabels[id] ?? id}`);
    if (shared.adel) lines.push('Adel');
    if (entity === 'personen' && personenState.dateMode === 'exact') {
      lines.push('Datums: alleen expliciet vastgelegd');
    }
    const periodLabel =
      get(periodKey) === 'all'
        ? ALL_PERIODS_LABEL
        : (facets.period ?? []).find((p) => p.key === get(periodKey))?.label ?? get(periodKey);
    lines.unshift(`Periode: ${periodLabel}`);
    return lines;
  });

  onMount(() => {
    const snap = loadOverviewSnapshot(entity);
    if (snap) {
      applySnapshot(snap);
      overviewReady = true;
    } else {
      const params = new URLSearchParams(window.location.search);
      const period = applyPeriodFromParams(params);
      if (period && period !== get(periodKey)) periodKey.set(period);
      if (entity === 'personen') {
        personenState = parsePersonenParams(params);
      } else {
        aanstellingenState = parseAanstellingenParams(params);
      }
      trackedPeriod = get(periodKey);
      void refreshSearch().finally(() => {
        overviewReady = true;
      });
    }

    periodUnsub = periodKey.subscribe((p) => {
      if (!overviewReady || p === trackedPeriod) return;
      trackedPeriod = p;
      updateOverviewSnapshot({ period: p });
      void refreshSearch();
    });

    return () => {
      periodUnsub?.();
    };
  });
</script>

<section class="overview-page">
  <header class="overview-header">
    <div>
      <p class="overview-kicker">Grafisch overzicht</p>
      <h2>{title}</h2>
    </div>
    <a class="btn-ghost" href={listBackHref}>← Terug naar lijst</a>
  </header>

  {#if error}
    <p class="err">{error} — start API with <code>./scripts/dev.sh</code></p>
  {/if}

  {#if loading && !hasSearched}
    <p class="hint">Laden…</p>
  {:else if hasSearched}
    {#if total !== null}
      <div class="overview-meta">
        <p class="count">{total} treffers</p>
        {#if queryLines.length}
          <ul class="query-summary">
            {#each queryLines as line}
              <li>{line}</li>
            {/each}
          </ul>
        {/if}
      </div>
    {/if}

    <div class="overview-charts" class:loading={loading}>
      <FacetSummary
        {entity}
        {facets}
        periodMode={$periodMode}
        {hasSearched}
        {total}
        {timeline}
        {timelineMeta}
        {includeShadowDates}
        onselect={onFacetToggle}
        {onTimelineSelect}
      />
    </div>

    <footer class="overview-footnotes">
      <p>
        Klik op een staaf om filters toe te passen. Open de tabel via
        <a href={listBackHref}>Terug naar lijst</a>.
      </p>
      {#if entity === 'personen' && personenState.dateMode === 'exact'}
        <p>Geboortejaargrafiek telt alleen expliciet vastgelegde geboortejaren.</p>
      {/if}
    </footer>
  {/if}
</section>

<style>
  .overview-charts.loading {
    opacity: 0.65;
    pointer-events: none;
  }
</style>
