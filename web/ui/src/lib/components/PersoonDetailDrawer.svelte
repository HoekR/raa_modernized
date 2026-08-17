<script lang="ts">
  import Drawer from '$lib/components/Drawer.svelte';
  import PersoonDetailBody from '$lib/components/PersoonDetailBody.svelte';
  import { fetchPersoonCached, type PersoonDetail } from '$lib/detail';

  let {
    open = $bindable(false),
    personId = $bindable(null as number | null),
  }: {
    open?: boolean;
    personId?: number | null;
  } = $props();

  let person = $state<PersoonDetail | null>(null);
  let loading = $state(false);
  let error = $state<string | null>(null);

  async function load(id: number) {
    loading = true;
    error = null;
    person = null;
    try {
      person = await fetchPersoonCached(id);
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      loading = false;
    }
  }

  $effect(() => {
    if (open && personId != null) load(personId);
    if (!open) {
      person = null;
      error = null;
    }
  });
</script>

<Drawer bind:open title={person?.display_naam ? String(person.display_naam) : 'Persoon'} wide>
  {#if loading}
    <p class="hint">Laden…</p>
  {:else if error}
    <p class="err">{error}</p>
  {:else if person}
    <PersoonDetailBody {person} compact />
  {/if}
  {#snippet footer()}
    {#if personId != null}
      <a href="/personen/{personId}">Volledige pagina →</a>
    {/if}
  {/snippet}
</Drawer>
