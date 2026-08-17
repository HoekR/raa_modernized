<script lang="ts">
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { isLoggedIn } from '$lib/auth';
  import {
    fetchToelichtingContext,
    revertAmendment,
    saveToelichting,
    type ToelichtingEditContext,
  } from '$lib/editorial';

  let ctx = $state<ToelichtingEditContext | null>(null);
  let draft = $state('');
  let note = $state('');
  let tab = $state<'edit' | 'preview' | 'base'>('edit');
  let loading = $state(true);
  let saving = $state(false);
  let error = $state<string | null>(null);
  let message = $state<string | null>(null);

  async function load(id: string) {
    if (!isLoggedIn()) {
      goto('/login');
      return;
    }
    loading = true;
    error = null;
    message = null;
    ctx = null;
    try {
      const data = await fetchToelichtingContext(id);
      ctx = data;
      draft = data.toelichting_effective ?? data.toelichting_base ?? '';
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

  async function save() {
    if (!ctx) return;
    saving = true;
    error = null;
    message = null;
    try {
      await saveToelichting(ctx.id, draft, note || undefined);
      message = 'Opgeslagen.';
      await load(String(ctx.id));
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      saving = false;
    }
  }

  async function revert() {
    if (!ctx?.amendment || typeof ctx.amendment.id !== 'number') return;
    saving = true;
    error = null;
    try {
      await revertAmendment(ctx.amendment.id as number);
      message = 'Wijziging teruggedraaid.';
      await load(String(ctx.id));
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      saving = false;
    }
  }
</script>

<a href="/">← Dashboard</a>

{#if loading}
  <p class="hint">Laden…</p>
{:else if error}
  <p class="err">{error}</p>
{:else if ctx}
  <div class="panel">
    <h2>{ctx.naam}</h2>
    <p class="hint">Instelling #{ctx.id}{#if ctx.toelichting_amended} <span class="badge">bewerkt</span>{/if}</p>
  </div>

  <div class="tabs">
    <button type="button" class="tab" class:active={tab === 'edit'} onclick={() => (tab = 'edit')}>Bewerken</button>
    <button type="button" class="tab" class:active={tab === 'preview'} onclick={() => (tab = 'preview')}>Voorbeeld (publiek)</button>
    <button type="button" class="tab" class:active={tab === 'base'} onclick={() => (tab = 'base')}>Import-basis</button>
  </div>

  <div class="panel">
    {#if tab === 'edit'}
      <label>
        <span class="hint">Toelichting (HTML)</span>
        <textarea bind:value={draft}></textarea>
      </label>
      <label>
        <span class="hint">Wijzigingsnotitie (optioneel)</span>
        <input type="text" bind:value={note} />
      </label>
      <div class="btn-row">
        <button type="button" class="primary" disabled={saving} onclick={save}>Opslaan</button>
        {#if ctx.toelichting_amended && ctx.amendment}
          <button type="button" disabled={saving} onclick={revert}>Terug naar import</button>
        {/if}
      </div>
    {:else if tab === 'preview'}
      <div class="preview-html">{@html draft || '<p class="hint">—</p>'}</div>
    {:else}
      <div class="preview-html">{@html ctx.toelichting_base || '<p class="hint">—</p>'}</div>
    {/if}
    {#if message}
      <p class="hint">{message}</p>
    {/if}
  </div>

  {#if ctx.history.length}
    <div class="panel">
      <h2>Geschiedenis</h2>
      <ul>
        {#each ctx.history as h}
          <li>
            {h.status} — {h.editor_id} — {h.updated_at}
            {#if h.note}
              <em>({h.note})</em>
            {/if}
          </li>
        {/each}
      </ul>
    </div>
  {/if}
{/if}
