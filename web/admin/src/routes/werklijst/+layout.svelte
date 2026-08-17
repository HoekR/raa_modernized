<script lang="ts">
  let { children } = $props();
</script>

<div class="grid-page">
  {@render children()}
</div>

<style>
  :global(.admin-shell:has(.grid-page)) {
    max-width: none;
  }
</style>
