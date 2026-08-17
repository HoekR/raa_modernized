<script lang="ts">
  import { lifeCell } from '$lib/search';
  import type { LifeSummary } from '$lib/detail';

  let {
    subject,
    lifeSummary,
    stand,
  }: {
    subject: Record<string, unknown>;
    lifeSummary?: LifeSummary;
    stand?: string | null;
  } = $props();

  const geb = $derived(lifeCell(subject, 'geboorte'));
  const ovl = $derived(lifeCell(subject, 'overlijden'));
</script>

<div class="life-dates">
  <div class="item">
    <span class="field-label">Geboren</span>
    <div
      class="val"
      class:estimated={!lifeSummary?.geboorte && geb.estimated}
      title={geb.estimated ? 'Geschat uit aanstellingen' : undefined}
    >
      {lifeSummary?.geboorte ?? geb.text}
    </div>
  </div>
  <div class="item">
    <span class="field-label">Overleden</span>
    <div
      class="val"
      class:estimated={!lifeSummary?.overlijden && ovl.estimated}
      title={ovl.estimated ? 'Geschat uit aanstellingen' : undefined}
    >
      {lifeSummary?.overlijden ?? ovl.text}
    </div>
  </div>
  {#if stand}
    <div class="item">
      <span class="field-label">Stand</span>
      <div class="val">{stand}</div>
    </div>
  {/if}
</div>
