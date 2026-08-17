<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { isLoggedIn } from '$lib/auth';
  import { fetchConflicts, resolveConflict, type ConflictRow } from '$lib/editorial';

  let rows = $state<ConflictRow[]>([]);
  let error = $state<string | null>(null);
  let loading = $state(true);

  async function load() {
    if (!isLoggedIn()) {
      goto('/login');
      return;
    }
    loading = true;
    try {
      rows = await fetchConflicts();
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      loading = false;
    }
  }

  onMount(load);

  async function resolve(id: number, resolution: 'keep_amendment' | 'accept_base') {
    await resolveConflict(id, resolution);
    await load();
  }
</script>

<a href="/">← Dashboard</a>

<div class="panel">
  <h2>Importconflicten</h2>
  <p class="hint">Verschil tussen uw wijziging en een nieuwe extab-import.</p>
</div>

{#if loading}
  <p class="hint">Laden…</p>
{:else if error}
  <p class="err">{error}</p>
{:else if !rows.length}
  <p class="hint">Geen open conflicten.</p>
{:else}
  {#each rows as row}
    <div class="panel">
      <p>
        <strong>{row.entity_type} #{row.entity_id}</strong> — {row.field}
        <span class="hint"> (release {row.release_id})</span>
      </p>
      <div class="diff-grid">
        <div>
          <p class="hint">Oude basis</p>
          <pre class="preview-html">{row.old_base_value ?? '—'}</pre>
        </div>
        <div>
          <p class="hint">Nieuwe import</p>
          <pre class="preview-html">{row.new_base_value ?? '—'}</pre>
        </div>
        <div>
          <p class="hint">Uw amendment</p>
          <pre class="preview-html">{row.amendment_value ?? '—'}</pre>
        </div>
      </div>
      <div class="btn-row">
        <button type="button" class="primary" onclick={() => resolve(row.id, 'keep_amendment')}>
          Amendment behouden
        </button>
        <button type="button" onclick={() => resolve(row.id, 'accept_base')}>
          Nieuwe import accepteren
        </button>
        <a class="btn" href="/{row.entity_type}/{row.entity_id}">Naar editor</a>
      </div>
    </div>
  {/each}
{/if}
