<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { appPath } from '$lib/appPath';
  import { isLoggedIn } from '$lib/auth';
  import { fetchRecentAmendments } from '$lib/editorial';

  let rows = $state<Array<Record<string, unknown>>>([]);
  let error = $state<string | null>(null);
  let jumpId = $state('');
  let personId = $state('');

  onMount(async () => {
    if (!isLoggedIn()) {
      goto(appPath('/login'));
      return;
    }
    try {
      rows = await fetchRecentAmendments();
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    }
  });

  function openInstelling(e: Event) {
    e.preventDefault();
    const id = jumpId.trim();
    if (id) goto(appPath(`/instellingen/${id}`));
  }
</script>

<div class="panel">
  <h2>Dashboard</h2>
  <p class="hint">Redactiewerkplek — geen zoek-UI; open een record op id.</p>
  <form onsubmit={openInstelling} class="btn-row">
    <input type="text" bind:value={jumpId} placeholder="Instelling-id" />
    <button type="submit" class="primary">Instelling bewerken</button>
  </form>
  <form
    class="btn-row"
    onsubmit={(e) => {
      e.preventDefault();
      if (personId.trim()) goto(appPath(`/persoon/${personId.trim()}`));
    }}
  >
    <input type="text" bind:value={personId} placeholder="Persoon-id" />
    <button type="submit" class="primary">Persoon bewerken</button>
  </form>
  <p><a href={appPath('/conflicts')}>Importconflicten →</a> · <a href={appPath('/werklijst/personen')}>Werklijst (grid) →</a></p>
</div>

{#if error}
  <p class="err">{error}</p>
{:else if rows.length}
  <div class="panel">
    <h2>Recente wijzigingen</h2>
    <ul>
      {#each rows as row}
        <li>
          {#if row.entity_type === 'instelling' && row.field === 'toelichting'}
            <a href={appPath(`/instellingen/${row.entity_id}`)}>{row.entity_type} #{row.entity_id}</a>
          {:else if row.entity_type === 'persoon'}
            <a href={appPath(`/persoon/${row.entity_id}`)}>{row.entity_type} #{row.entity_id}</a> — {row.field}
          {:else if row.entity_type === 'aanstelling'}
            <a href={appPath(`/aanstelling/${row.entity_id}`)}>{row.entity_type} #{row.entity_id}</a> — {row.field}
          {:else}
            {row.entity_type} #{row.entity_id} — {row.field}
          {/if}
          <span class="hint"> ({row.updated_at ?? row.created_at})</span>
        </li>
      {/each}
    </ul>
  </div>
{:else}
  <p class="hint">Nog geen actieve wijzigingen.</p>
{/if}
