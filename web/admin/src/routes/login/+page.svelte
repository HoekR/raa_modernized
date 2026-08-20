<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { appPath } from '$lib/appPath';
  import { isLoggedIn, setApiKey } from '$lib/auth';

  let key = $state('');
  let error = $state<string | null>(null);

  onMount(() => {
    if (isLoggedIn()) goto(appPath('/'));
  });

  function submit(e: Event) {
    e.preventDefault();
    error = null;
    if (!key.trim()) {
      error = 'Voer een API-sleutel in.';
      return;
    }
    setApiKey(key);
    goto(appPath('/'));
  }
</script>

<div class="panel" style="max-width: 28rem">
  <h2>Inloggen</h2>
  <p class="hint">
    Voer de API-sleutel in uit <code>config.local.toml</code> (<code>[editorial].api_key</code>).
  </p>
  <form onsubmit={submit}>
    <label>
      <span class="hint">API-sleutel</span>
      <input type="password" bind:value={key} autocomplete="off" />
    </label>
    {#if error}
      <p class="err">{error}</p>
    {/if}
    <div class="btn-row">
      <button type="submit" class="primary">Doorgaan</button>
    </div>
  </form>
</div>
