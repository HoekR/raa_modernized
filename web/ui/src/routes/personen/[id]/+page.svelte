<script lang="ts">
  import { page } from '$app/stores';
  import PersoonDetailBody from '$lib/components/PersoonDetailBody.svelte';
  import { fetchPersoon, type PersoonDetail } from '$lib/detail';

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
</script>

<div class="detail-route">
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

      <div class="detail-block">
        <PersoonDetailBody {person} />
      </div>
    </article>
  {/if}
</div>

<style>
  .detail-block {
    padding: 0.85rem 0 0;
  }
</style>
