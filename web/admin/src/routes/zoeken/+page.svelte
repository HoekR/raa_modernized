<script lang="ts">
  import { goto } from '$app/navigation';
  import { appPath } from '$lib/appPath';
  import { isLoggedIn } from '$lib/auth';

  let instellingId = $state('');
  let personId = $state('');
  let aanstellingId = $state('');

  $effect(() => {
    if (!isLoggedIn()) goto(appPath('/login'));
  });

  function openInstelling(e: Event) {
    e.preventDefault();
    const id = instellingId.trim();
    if (id) goto(appPath(`/instellingen/${id}`));
  }

  function openPersoon(e: Event) {
    e.preventDefault();
    const id = personId.trim();
    if (id) goto(appPath(`/persoon/${id}`));
  }

  function openAanstelling(e: Event) {
    e.preventDefault();
    const id = aanstellingId.trim();
    if (id) goto(appPath(`/aanstelling/${id}`));
  }
</script>

<div class="panel">
  <h2>Record openen</h2>
  <form onsubmit={openInstelling}>
    <input type="text" bind:value={instellingId} placeholder="Instelling-id" />
    <div class="btn-row">
      <button type="submit" class="primary">Instelling (toelichting)</button>
    </div>
  </form>
  <form onsubmit={openPersoon}>
    <input type="text" bind:value={personId} placeholder="Persoon-id" />
    <div class="btn-row">
      <button type="submit" class="primary">Persoon</button>
    </div>
  </form>
  <form onsubmit={openAanstelling}>
    <input type="text" bind:value={aanstellingId} placeholder="Aanstelling-id" />
    <div class="btn-row">
      <button type="submit" class="primary">Aanstelling</button>
    </div>
  </form>
</div>
