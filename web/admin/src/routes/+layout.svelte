<script lang="ts">
  import '../app.css';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { appPath } from '$lib/appPath';
  import { isLoggedIn, clearApiKey } from '$lib/auth';

  let { children } = $props();

  function logout() {
    clearApiKey();
    goto(appPath('/login'));
  }

  const onLogin = $derived($page.url.pathname === appPath('/login'));
</script>

<div class="admin-shell">
  <header class="admin-header">
    <h1>RAA — Redactie</h1>
    {#if !onLogin && isLoggedIn()}
      <nav class="admin-nav">
        <a href={appPath('/')}>Dashboard</a>
        <a href={appPath('/werklijst/personen')}>Werklijst</a>
        <a href={appPath('/conflicts')}>Conflicten</a>
        <a href={appPath('/zoeken')}>Openen op id</a>
        <button type="button" onclick={logout}>Uitloggen</button>
      </nav>
    {/if}
  </header>
  {@render children()}
</div>
