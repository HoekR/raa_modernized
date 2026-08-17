<script lang="ts">
  import LifeDatesRow from '$lib/components/LifeDatesRow.svelte';
  import AanstellingenTable from '$lib/components/AanstellingenTable.svelte';
  import type { PersoonDetail } from '$lib/detail';

  let {
    person,
    compact = false,
    maxAanstellingen = 0,
  }: {
    person: PersoonDetail;
    compact?: boolean;
    maxAanstellingen?: number;
  } = $props();

  const stand = $derived(
    typeof person.stand === 'string' ? person.stand : (person.stand_naam as string | undefined)
  );
</script>

<LifeDatesRow subject={person} lifeSummary={person.life_summary} stand={stand} />

{#if compact}
  <section class="detail-section" style="margin-top:1rem;padding-top:0;border-top:0">
    <h2 style="font-size:0.95rem">Bovenlokale aanstellingen</h2>
    <AanstellingenTable
      rows={person.aanstellingen_bovenlokaal ?? []}
      compact
      maxRows={maxAanstellingen}
    />
  </section>
{:else}
  {#if person.aliassen?.length}
    <details class="detail-collapsible">
      <summary>Aliassen ({person.aliassen.length})</summary>
      <div class="detail-collapsible-body">
        <ul class="detail-aliases">
          {#each person.aliassen as a}
            <li>{a.naam}</li>
          {/each}
        </ul>
      </div>
    </details>
  {/if}

  {#if person.opmerkingen_html}
    <details class="detail-collapsible">
      <summary>Opmerkingen</summary>
      <div class="detail-collapsible-body detail-prose">{@html person.opmerkingen_html}</div>
    </details>
  {/if}

  {#if person.bronnen?.length}
    <details class="detail-collapsible">
      <summary>Bronnen ({person.bronnen.length})</summary>
      <div class="detail-collapsible-body detail-bronnen">
        {#each person.bronnen as b}
          <p>{b.naam}{b.details ? ` ${b.details}` : ''}</p>
        {/each}
      </div>
    </details>
  {/if}

  {#if person.aanstellingen_lokaal?.length}
    <details class="detail-collapsible">
      <summary>Lokale aanstellingen ({person.aanstellingen_lokaal.length})</summary>
      <div class="detail-collapsible-body">
        <AanstellingenTable rows={person.aanstellingen_lokaal} compact />
      </div>
    </details>
  {/if}

  <section class="detail-section">
    <h2>Bovenlokale aanstellingen</h2>
    <AanstellingenTable rows={person.aanstellingen_bovenlokaal ?? []} />
  </section>
{/if}
