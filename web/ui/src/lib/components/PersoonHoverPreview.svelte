<script lang="ts">
  import HoverPreview from '$lib/components/HoverPreview.svelte';
  import PersoonDetailBody from '$lib/components/PersoonDetailBody.svelte';
  import { fetchPersoonCached, type PersoonDetail } from '$lib/detail';

  let {
    personId = null,
    anchorTop = 0,
    open = false,
    onenter,
    onleave,
  }: {
    personId?: number | null;
    anchorTop?: number;
    open?: boolean;
    onenter?: () => void;
    onleave?: () => void;
  } = $props();

  let person = $state<PersoonDetail | null>(null);
  let loading = $state(false);
  let error = $state<string | null>(null);
  let loadedId = $state<number | null>(null);

  async function load(id: number) {
    loading = true;
    error = null;
    try {
      const data = await fetchPersoonCached(id);
      if (id !== personId) return;
      person = data;
      loadedId = id;
    } catch (e) {
      if (id !== personId) return;
      error = e instanceof Error ? e.message : String(e);
      person = null;
    } finally {
      if (id === personId) loading = false;
    }
  }

  $effect(() => {
    if (open && personId != null) {
      if (loadedId !== personId) load(personId);
    } else if (!open) {
      person = null;
      error = null;
      loadedId = null;
    }
  });

  const title = $derived(
    person?.display_naam ? String(person.display_naam) : 'Persoon'
  );
</script>

<HoverPreview
  {open}
  {anchorTop}
  {title}
  href={personId != null ? `/personen/${personId}` : undefined}
  {onenter}
  {onleave}
>
  {#if loading && !person}
    <p class="hint">Laden…</p>
  {:else if error}
    <p class="err">{error}</p>
  {:else if person}
    {#if person.heerlijkheid_line}
      <p class="hover-preview-sub">{person.heerlijkheid_line}</p>
    {/if}
    <PersoonDetailBody {person} compact maxAanstellingen={4} />
  {/if}
</HoverPreview>
