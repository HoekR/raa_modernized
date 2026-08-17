<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { isLoggedIn } from '$lib/auth';
  import {
    fetchEntityContext,
    PERSOON_DATE_GROUPS,
    revertAmendment,
    saveBatch,
    saveField,
    type EntityEditContext,
    type FieldEditState,
  } from '$lib/editorial';

  let ctx = $state<EntityEditContext | null>(null);
  let drafts = $state<Record<string, string>>({});
  let note = $state('');
  let loading = $state(true);
  let saving = $state(false);
  let error = $state<string | null>(null);
  let message = $state<string | null>(null);

  const entityType = $derived($page.params.entity ?? '');
  const entityId = $derived($page.params.id ?? '');

  const dateGroupFields = $derived(
    new Set(PERSOON_DATE_GROUPS.flatMap((g) => g.fields))
  );

  const scalarFields = $derived.by(() => {
    if (!ctx) return [] as Array<[string, FieldEditState]>;
    return Object.entries(ctx.fields).filter(([name]) => !dateGroupFields.has(name));
  });

  async function load() {
    if (!isLoggedIn()) {
      goto('/login');
      return;
    }
    loading = true;
    error = null;
    message = null;
    try {
      const data = await fetchEntityContext(entityType, entityId);
      ctx = data;
      const d: Record<string, string> = {};
      for (const [key, field] of Object.entries(data.fields)) {
        d[key] = field.effective != null ? String(field.effective) : '';
      }
      drafts = d;
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      loading = false;
    }
  }

  $effect(() => {
    if (entityType && entityId) load();
  });

  function isDirty(field: string): boolean {
    if (!ctx) return false;
    const effective = ctx.fields[field]?.effective;
    return (drafts[field] ?? '') !== (effective != null ? String(effective) : '');
  }

  async function saveFieldKey(field: string) {
    if (!ctx) return;
    saving = true;
    error = null;
    message = null;
    try {
      await saveField(ctx.entity_type, ctx.id, field, drafts[field] ?? '', note || undefined);
      message = `${field} opgeslagen.`;
      await load();
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      saving = false;
    }
  }

  async function saveDateGroup(groupLabel: string, fields: string[]) {
    if (!ctx) return;
    const changes = fields
      .filter((field) => isDirty(field))
      .map((field) => ({
        entity_type: ctx!.entity_type,
        entity_id: ctx!.id,
        field,
        value: drafts[field] ?? '',
      }));
    if (!changes.length) {
      message = 'Geen wijzigingen in deze datumgroep.';
      return;
    }
    saving = true;
    error = null;
    message = null;
    try {
      const result = await saveBatch(changes, note || undefined);
      if (result.errors.length) {
        error = result.errors.map((e) => `${e.field}: ${e.error}`).join('; ');
      } else {
        message = `${groupLabel} opgeslagen (${result.applied.length + result.reverted.length} velden).`;
      }
      await load();
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      saving = false;
    }
  }

  async function revertField(field: string) {
    const amendId = ctx?.fields[field]?.amendment_id;
    if (!amendId) return;
    saving = true;
    try {
      await revertAmendment(amendId);
      message = `${field} teruggedraaid.`;
      await load();
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
    <h2>{ctx.label}</h2>
    <p class="hint">{ctx.entity_type} #{ctx.id}</p>
    <label>
      <span class="hint">Wijzigingsnotitie (optioneel)</span>
      <input type="text" bind:value={note} />
    </label>
  </div>

  {#each scalarFields as [fieldName, field]}
    <div class="panel">
      <h2>
        {fieldName}
        {#if field.amended}<span class="badge">bewerkt</span>{/if}
      </h2>
      <div class="diff-grid">
        <div>
          <p class="hint">Import-basis</p>
          <pre class="preview-html">{field.base ?? '—'}</pre>
        </div>
        <div>
          <p class="hint">Draft</p>
          <textarea bind:value={drafts[fieldName]} rows="3"></textarea>
        </div>
      </div>
      <div class="btn-row">
        <button type="button" class="primary" disabled={saving} onclick={() => saveFieldKey(fieldName)}>
          Opslaan
        </button>
        {#if field.amended && field.amendment_id}
          <button type="button" disabled={saving} onclick={() => revertField(fieldName)}>
            Terug naar import
          </button>
        {/if}
      </div>
    </div>
  {/each}

  {#if ctx.entity_type === 'persoon'}
    {#each PERSOON_DATE_GROUPS as group}
      {@const groupLabel = group.label ?? 'datum'}
      <div class="panel">
        <h2>{groupLabel} <span class="hint">(exact: j / m / d)</span></h2>
        <div class="date-parts">
          {#each group.fields as fieldName, idx}
            {@const field = ctx.fields[fieldName]}
            {#if field}
              <label class="date-part">
                <span class="hint">{['j', 'm', 'd'][idx]}</span>
                <input type="text" bind:value={drafts[fieldName]} />
                {#if field.amended}<span class="badge">bewerkt</span>{/if}
              </label>
            {/if}
          {/each}
        </div>
        <p class="hint">Basis: {group.fields.map((f) => ctx!.fields[f]?.base || '—').join(' / ')}</p>
        <div class="btn-row">
          <button
            type="button"
            class="primary"
            disabled={saving}
            onclick={() => saveDateGroup(groupLabel, group.fields)}
          >
            Opslaan {groupLabel}
          </button>
        </div>
      </div>
    {/each}
  {/if}

  {#if message}
    <p class="hint">{message}</p>
  {/if}
{/if}

<style>
  .date-parts {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin-bottom: 0.5rem;
  }

  .date-part {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    min-width: 4.5rem;
  }

  .date-part input {
    max-width: 5rem;
  }
</style>
