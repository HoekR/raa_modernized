<script lang="ts">
  import '../app.css';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { isLoggedIn, clearApiKey } from '$lib/auth';

  let { children } = $props();

  function logout() {
    clearApiKey();
    goto('/login');
  }

  const onLogin = $derived($page.url.pathname.startsWith('/login'));
</script>

<div class="admin-shell">
  <header class="admin-header">
    <h1>RAA — Redactie</h1>
    {#if !onLogin && isLoggedIn()}
      <nav class="admin-nav">
        <a href="/">Dashboard</a>
        <a href="/werklijst/personen">Werklijst</a>
        <a href="/conflicts">Conflicten</a>
        <a href="/zoeken">Openen op id</a>
        <button type="button" onclick={logout}>Uitloggen</button>
      </nav>
    {/if}
  </header>
  {@render children()}
</div>
