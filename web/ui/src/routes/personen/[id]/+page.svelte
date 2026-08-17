<script lang="ts">
  import { page } from '$app/stores';
  import {
    fetchPersoon,
    formatNamens,
    type AanstellingDetail,
    type PersoonDetail,
  } from '$lib/detail';
  import { lifeCell as lifeCellSearch } from '$lib/search';
  let person = $state<PersoonDetail | null>(null);
  let error = $state<string | null>(null);
  let loading = $state(true);

  async function load(id: string) {
    loading = true;
    error = null;
    person = null;
    try {
      person = await fetchPersoon(id);
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      loading = false;
    }
  }

  $effect(() => {
    const id = $page.params.id;
    if (id) load(id);
  });

  function othersHref(a: AanstellingDetail): string {
    const params = new URLSearchParams();
    if (a.functie_id != null) params.set('functie_id', String(a.functie_id));
    if (a.instelling_id != null) params.set('instelling_id', String(a.instelling_id));
    return `/aanstellingen?${params}`;
  }
</script>

{#if loading}
  <p class="hint">Laden…</p>
{:else if error}
  <p class="err">{error}</p>
  <a class="detail-back" href="/personen">← Terug naar personen</a>
{:else if person}
  <a class="detail-back" href="/personen">← Terug naar personen</a>

  <article class="detail">
    <header class="detail-hero">
      <p class="detail-kicker">Persoon</p>
      <h1>{person.display_naam || '—'}</h1>
      {#if person.heerlijkheid_line}
        <p class="detail-subtitle">{person.heerlijkheid_line}</p>
      {/if}
    </header>

    <div class="detail-life">
      {#if person.life_summary?.geboorte}
        <p>{person.life_summary.geboorte}</p>
      {:else}
        {@const geb = lifeCellSearch(person, 'geboorte')}
        <p>
          geboren:
          <span class:estimated={geb.estimated}>{geb.text}</span>
        </p>
      {/if}
      {#if person.life_summary?.overlijden}
        <p>{person.life_summary.overlijden}</p>
      {:else}
        {@const ovl = lifeCellSearch(person, 'overlijden')}
        <p>
          overleden:
          <span class:estimated={ovl.estimated}>{ovl.text}</span>
        </p>
      {/if}
    </div>

    {#if person.aliassen?.length}
      <section class="detail-section">
        <h2>Aliassen</h2>
        <ul class="detail-aliases">
          {#each person.aliassen as a}
            <li>{a.naam}</li>
          {/each}
        </ul>
      </section>
    {/if}

    {#if person.opmerkingen_html}
      <section class="detail-section">
        <h2>Opmerkingen</h2>
        <div class="detail-prose">{@html person.opmerkingen_html}</div>
      </section>
    {/if}

    {#if person.bronnen?.length}
      <section class="detail-section">
        <h2>Bronnen</h2>
        <div class="detail-bronnen">
          {#each person.bronnen as b}
            <p>{b.naam}{b.details ? ` ${b.details}` : ''}</p>
          {/each}
        </div>
      </section>
    {/if}

    {#if person.aanstellingen_lokaal?.length}
      <section class="detail-section">
        <h2>Lokale aanstellingen</h2>
        <ul class="detail-lokaal">
          {#each person.aanstellingen_lokaal as a}
            <li>
              {a.functie || '?'}
              {a.instelling || ''}
              ({a.van_als_bekend || '?'} – {a.tot_als_bekend || '?'})
              {#if a.opmerkingen}
                — {a.opmerkingen}
              {/if}
            </li>
          {/each}
        </ul>
      </section>
    {/if}

    <section class="detail-section">
      <h2>Bovenlokale aanstellingen</h2>
      {#if !person.aanstellingen_bovenlokaal?.length}
        <p class="detail-empty">Geen bovenlokale aanstellingen</p>
      {:else}
        {#each person.aanstellingen_bovenlokaal as a}
          <div class="detail-aanstelling">
            <dl>
              <dt>Functie</dt>
              <dd>
                {#if a.functie_id}
                  <a href="/functies/{a.functie_id}">{a.functie || '?'}</a>
                {:else}
                  {a.functie || '?'}
                {/if}
              </dd>
              {#if a.instelling}
                <dt>Instelling</dt>
                <dd>
                  {#if a.instelling_id}
                    <a href="/instellingen/{a.instelling_id}">{a.instelling}</a>
                  {:else}
                    {a.instelling}
                  {/if}
                </dd>
              {/if}
              <dt>Van–tot</dt>
              <dd>{a.van_als_bekend || '?'} – {a.tot_als_bekend || '?'}</dd>
              {#if formatNamens(a)}
                <dt>Namens</dt>
                <dd>{formatNamens(a)}</dd>
              {/if}
            </dl>
            <p>
              <a href={othersHref(a)}>anderen met deze aanstelling…</a>
            </p>
            {#if a.opmerkingen_html}
              <div class="opmerkingen">{@html a.opmerkingen_html}</div>
            {:else if a.opmerkingen}
              <p class="opmerkingen">{a.opmerkingen}</p>
            {/if}
          </div>
        {/each}
      {/if}
    </section>
  </article>
{/if}
