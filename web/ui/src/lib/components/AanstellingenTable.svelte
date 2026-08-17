<script lang="ts">
  import { formatNamens, type AanstellingDetail } from '$lib/detail';

  let {
    rows,
    compact = false,
  }: {
    rows: AanstellingDetail[];
    compact?: boolean;
  } = $props();

  let expanded = $state<number | null>(null);

  function othersHref(a: AanstellingDetail): string {
    const params = new URLSearchParams();
    if (a.functie_id != null) params.set('functie_id', String(a.functie_id));
    if (a.instelling_id != null) params.set('instelling_id', String(a.instelling_id));
    return `/aanstellingen?${params}`;
  }

  function hasNote(a: AanstellingDetail): boolean {
    return Boolean(a.opmerkingen_html || a.opmerkingen);
  }
</script>

{#if !rows.length}
  <p class="detail-empty">Geen aanstellingen</p>
{:else}
  <table>
    <thead>
      <tr>
        <th>Functie</th>
        <th>Instelling</th>
        <th class="date">Van</th>
        <th class="date">Tot</th>
        {#if !compact}<th>Namens</th><th></th>{/if}
      </tr>
    </thead>
    <tbody>
      {#each rows as a, i}
        <tr>
          <td>
            {#if a.functie_id}
              <a href="/functies/{a.functie_id}">{a.functie || '?'}</a>
            {:else}
              {a.functie || '?'}
            {/if}
          </td>
          <td>
            {#if a.instelling_id}
              <a href="/instellingen/{a.instelling_id}">{a.instelling || '—'}</a>
            {:else}
              {a.instelling || '—'}
            {/if}
          </td>
          <td class="date">{a.van_als_bekend || '?'}</td>
          <td class="date">{a.tot_als_bekend || '?'}</td>
          {#if !compact}
            <td>{formatNamens(a) || '—'}</td>
            <td class="date" style="text-align:left;font-size:0.82rem">
              {#if hasNote(a)}
                <button
                  type="button"
                  class="btn-ghost"
                  style="padding:0.15rem 0.45rem;font-size:0.75rem"
                  onclick={() => (expanded = expanded === i ? null : i)}
                >
                  {expanded === i ? 'Minder' : 'Opmerking'}
                </button>
              {/if}
              <a href={othersHref(a)} style="margin-left:0.35rem">anderen…</a>
            </td>
          {/if}
        </tr>
        {#if !compact && expanded === i && hasNote(a)}
          <tr class="aanst-row-note">
            <td colspan="6">
              {#if a.opmerkingen_html}
                {@html a.opmerkingen_html}
              {:else}
                {a.opmerkingen}
              {/if}
            </td>
          </tr>
        {/if}
      {/each}
    </tbody>
  </table>
{/if}
