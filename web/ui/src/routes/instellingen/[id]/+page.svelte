<script lang="ts">
  import { page } from '$app/stores';
  import EntityProfile from '$lib/components/EntityProfile.svelte';
  import { fetchInstelling, type EntityProfile as Profile } from '$lib/detail';

  let profile = $state<Profile | null>(null);
  let error = $state<string | null>(null);
  let loading = $state(true);

  async function load(id: string) {
    loading = true;
    error = null;
    profile = null;
    try {
      const data = await fetchInstelling(id);
      profile = data.profile ?? {
        entity_type: 'instelling',
        id: data.id,
        naam: data.naam,
      };
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

{#if loading}
  <p class="hint">Laden…</p>
{:else if error}
  <p class="err">{error}</p>
  <a class="detail-back" href="/instellingen">← Terug naar instellingen</a>
{:else if profile}
  <a class="detail-back" href="/instellingen">← Terug naar instellingen</a>
  <EntityProfile {profile} />
{/if}
