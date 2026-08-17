<script lang="ts">
  import { goto } from '$app/navigation';
  import { isLoggedIn } from '$lib/auth';
  import {
    downloadPersoonTemplate,
    fetchBatch,
    fieldHeader,
    importPersoonFile,
    isDatePartField,
    parseIdList,
    saveBatch,
    type BatchChange,
    type GridBatchResponse,
    type GridRow,
    type ImportParseError,
  } from '$lib/editorial';

  let idInput = $state('');
  let note = $state('');
  let importNote = $state('');
  let importFile = $state<File | null>(null);
  let importLoading = $state(false);
  let importErrors = $state<ImportParseError[]>([]);
  let batch = $state<GridBatchResponse | null>(null);
  /** Draft values keyed by `${rowId}:${field}` */
  let drafts = $state<Record<string, string>>({});
  let loading = $state(false);
  let saving = $state(false);
  let error = $state<string | null>(null);
  let message = $state<string | null>(null);
  let saveErrors = $state<Array<{ row: number; field: string; error: string }>>([]);

  $effect(() => {
    if (!isLoggedIn()) goto('/login');
  });

  function draftKey(rowId: number, field: string) {
    return `${rowId}:${field}`;
  }

  function cellValue(row: GridRow, field: string): string {
    const key = draftKey(row.id, field);
    if (key in drafts) return drafts[key];
    return row.fields[field]?.effective ?? '';
  }

  function setCell(rowId: number, field: string, value: string) {
    drafts = { ...drafts, [draftKey(rowId, field)]: value };
  }

  function isDirty(row: GridRow, field: string): boolean {
    const key = draftKey(row.id, field);
    if (!(key in drafts)) return false;
    return drafts[key] !== (row.fields[field]?.effective ?? '');
  }

  function cellClass(row: GridRow, field: string): string {
    const parts: string[] = ['grid-cell'];
    const state = row.fields[field];
    if (isDirty(row, field)) parts.push('dirty');
    else if (state?.amended) parts.push('amended');
    return parts.join(' ');
  }

  async function loadGrid() {
    const ids = parseIdList(idInput);
    if (!ids.length) {
      error = 'Voer minstens één geldig persoon-id in.';
      return;
    }
    loading = true;
    error = null;
    message = null;
    saveErrors = [];
    try {
      const data = await fetchBatch('persoon', ids);
      batch = data;
      drafts = {};
      if (data.missing_ids.length) {
        message = `Niet gevonden: ${data.missing_ids.join(', ')}`;
      }
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
      batch = null;
    } finally {
      loading = false;
    }
  }

  function collectChanges(): BatchChange[] {
    if (!batch) return [];
    const changes: BatchChange[] = [];
    for (const row of batch.rows) {
      for (const field of batch.fields) {
        if (!isDirty(row, field)) continue;
        changes.push({
          entity_type: 'persoon',
          entity_id: row.id,
          field,
          value: cellValue(row, field),
        });
      }
    }
    return changes;
  }

  async function saveGrid() {
    const changes = collectChanges();
    if (!changes.length) {
      message = 'Geen wijzigingen om op te slaan.';
      return;
    }
    saving = true;
    error = null;
    message = null;
    saveErrors = [];
    try {
      const result = await saveBatch(changes, note || undefined);
      const parts: string[] = [];
      if (result.applied.length) parts.push(`${result.applied.length} opgeslagen`);
      if (result.reverted.length) parts.push(`${result.reverted.length} teruggedraaid`);
      if (result.skipped.length) parts.push(`${result.skipped.length} overgeslagen`);
      message = parts.join(', ') || 'Klaar.';
      if (result.errors.length) {
        saveErrors = result.errors.map((e) => ({
          row: e.entity_id,
          field: e.field,
          error: e.error,
        }));
      }
      await loadGrid();
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      saving = false;
    }
  }

  function handlePaste(e: ClipboardEvent, startRowIdx: number, startFieldIdx: number) {
    if (!batch) return;
    const text = e.clipboardData?.getData('text/plain');
    if (!text || (!text.includes('\t') && !text.includes('\n'))) return;
    e.preventDefault();
    const lines = text.replace(/\r/g, '').split('\n').filter((l) => l.length > 0);
    const next = { ...drafts };
    for (let ri = 0; ri < lines.length; ri++) {
      const row = batch.rows[startRowIdx + ri];
      if (!row) break;
      const cols = lines[ri].split('\t');
      for (let ci = 0; ci < cols.length; ci++) {
        const field = batch.fields[startFieldIdx + ci];
        if (!field) break;
        next[draftKey(row.id, field)] = cols[ci].trim();
      }
    }
    drafts = next;
  }

  const dirtyCount = $derived.by(() => {
    if (!batch) return 0;
    let n = 0;
    for (const row of batch.rows) {
      for (const field of batch.fields) {
        if (isDirty(row, field)) n++;
      }
    }
    return n;
  });

  async function downloadTemplate(prefill: boolean) {
    error = null;
    try {
      const ids = prefill ? parseIdList(idInput) : [];
      if (prefill && !ids.length) {
        error = 'Voer ids in voor export, of kies leeg sjabloon.';
        return;
      }
      await downloadPersoonTemplate(prefill ? ids : undefined);
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    }
  }

  async function runImport(dryRun: boolean) {
    if (!importFile) {
      error = 'Kies een .xlsx- of .csv-bestand.';
      return;
    }
    importLoading = true;
    error = null;
    message = null;
    importErrors = [];
    saveErrors = [];
    try {
      const result = await importPersoonFile(importFile, {
        dryRun,
        note: importNote || undefined,
      });
      if (result.parse_errors.length) {
        importErrors = result.parse_errors;
      }
      if (result.result?.errors.length) {
        saveErrors = result.result.errors.map((e) => ({
          row: e.entity_id,
          field: e.field,
          error: e.error,
        }));
      }
      const r = result.result;
      if (dryRun) {
        message = `Proefrun: ${result.person_count ?? 0} personen, ${result.change_count ?? 0} celwijzigingen.`;
        if (r && !r.errors.length) message += ' Geen validatiefouten.';
      } else if (r) {
        message = `Import: ${r.applied.length} opgeslagen, ${r.reverted.length} teruggedraaid.`;
        if (parseIdList(idInput).length) await loadGrid();
      }
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      importLoading = false;
    }
  }
</script>

<a href="/">← Dashboard</a>

<div class="panel">
  <h2>Werklijst — personen</h2>
  <p class="hint">
    Exacte datums als jaar / maand / dag (m en d optioneel). Na opslaan worden life dates en search display batch-gewijs ververst.
  </p>
  <label>
    <span class="hint">Persoon-ids</span>
    <textarea class="id-input" bind:value={idInput} placeholder="1988, 42, 1001…"></textarea>
  </label>
  <div class="btn-row">
    <button type="button" class="primary" disabled={loading} onclick={loadGrid}>Laden</button>
  </div>
</div>

<div class="panel">
  <h2>Excel / CSV import</h2>
  <p class="hint">
    Download het sjabloon (<code>raa_persoon_werklijst.xlsx</code>), bewerk in Excel, upload .xlsx of .csv.
    Kolomkoppen zijn vast — zie tabblad <em>uitleg</em>. Lege cellen = geen wijziging; <code>-</code> = veld leegmaken.
  </p>
  <div class="btn-row">
    <button type="button" onclick={() => downloadTemplate(false)}>Leeg sjabloon</button>
    <button type="button" onclick={() => downloadTemplate(true)}>Export ids → Excel</button>
  </div>
  <label>
    <span class="hint">Bestand (.xlsx / .csv)</span>
    <input
      type="file"
      accept=".xlsx,.xlsm,.csv,text/csv"
      onchange={(e) => {
        importFile = e.currentTarget.files?.[0] ?? null;
      }}
    />
  </label>
  <label>
    <span class="hint">Importnotitie (optioneel)</span>
    <input type="text" bind:value={importNote} />
  </label>
  <div class="btn-row">
    <button type="button" disabled={importLoading || !importFile} onclick={() => runImport(true)}>
      Proefrun
    </button>
    <button
      type="button"
      class="primary"
      disabled={importLoading || !importFile}
      onclick={() => runImport(false)}
    >
      Importeren
    </button>
  </div>
</div>

{#if batch?.rows.length}
  <div class="panel grid-toolbar">
    <label>
      <span class="hint">Wijzigingsnotitie (optioneel)</span>
      <input type="text" bind:value={note} />
    </label>
    <div class="btn-row">
      <button type="button" class="primary" disabled={saving || dirtyCount === 0} onclick={saveGrid}>
        Opslaan ({dirtyCount} cel{dirtyCount === 1 ? '' : 'len'})
      </button>
      <span class="hint">{batch.rows.length} rijen · {batch.fields.length} kolommen</span>
    </div>
  </div>

  <div class="grid-wrap">
    <table class="edit-grid">
      <thead>
        {#if batch.column_groups?.length}
          <tr>
            <th class="sticky col-id" rowspan="2">id</th>
            <th class="sticky col-label" rowspan="2">naam</th>
            {#each batch.column_groups as group}
              {#if group.label}
                <th colspan={group.fields.length}>{group.label}</th>
              {:else}
                {#each group.fields as field}
                  <th rowspan="2">{field}</th>
                {/each}
              {/if}
            {/each}
          </tr>
          <tr>
            {#each batch.column_groups as group}
              {#if group.label}
                {#each group.fields as field}
                  <th class:date-col={isDatePartField(field)}>
                    {fieldHeader(field, batch.field_labels)}
                  </th>
                {/each}
              {/if}
            {/each}
          </tr>
        {:else}
          <tr>
            <th class="sticky col-id">id</th>
            <th class="sticky col-label">naam</th>
            {#each batch.fields as field}
              <th>{field}</th>
            {/each}
          </tr>
        {/if}
      </thead>
      <tbody>
        {#each batch.rows as row, rowIdx}
          <tr>
            <td class="sticky col-id mono">{row.id}</td>
            <td class="sticky col-label" title={row.label}>{row.label}</td>
            {#each batch.fields as field, fieldIdx}
              <td class="{cellClass(row, field)}{isDatePartField(field) ? ' date-col' : ''}">
                <input
                  type="text"
                  class:date-input={isDatePartField(field)}
                  value={cellValue(row, field)}
                  oninput={(e) => setCell(row.id, field, e.currentTarget.value)}
                  onpaste={(e) => handlePaste(e, rowIdx, fieldIdx)}
                />
              </td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}

{#if loading}
  <p class="hint">Laden…</p>
{/if}
{#if error}
  <p class="err">{error}</p>
{/if}
{#if message}
  <p class="hint">{message}</p>
{/if}
{#if saveErrors.length}
  <div class="panel">
    <h2>Validatiefouten</h2>
    <ul>
      {#each saveErrors as err}
        <li class="err">#{err.row} · {err.field}: {err.error}</li>
      {/each}
    </ul>
  </div>
{/if}
{#if importErrors.length}
  <div class="panel">
    <h2>Importfouten</h2>
    <ul>
      {#each importErrors as err}
        <li class="err">
          rij {err.row}{#if err.column !== 'file' && err.column !== 'headers'} · {err.column}{/if}: {err.error}
        </li>
      {/each}
    </ul>
  </div>
{/if}

<style>
  .id-input {
    min-height: 4.5rem;
    font-family: var(--mono);
  }

  .grid-wrap {
    overflow: auto;
    max-height: calc(100vh - 14rem);
    border: 1px solid var(--line);
    border-radius: 4px;
    background: var(--surface);
  }

  .edit-grid {
    border-collapse: collapse;
    width: max-content;
    min-width: 100%;
    font-size: 0.85rem;
  }

  .edit-grid th,
  .edit-grid td {
    border: 1px solid var(--line);
    padding: 0;
    vertical-align: top;
  }

  .edit-grid th {
    background: var(--paper);
    padding: 0.35rem 0.5rem;
    font-weight: 600;
    position: sticky;
    top: 0;
    z-index: 2;
  }

  .edit-grid .sticky {
    position: sticky;
    background: var(--surface);
    z-index: 1;
  }

  .edit-grid thead .sticky {
    z-index: 3;
    background: var(--paper);
  }

  .col-id {
    left: 0;
    min-width: 4rem;
  }

  .col-label {
    left: 4rem;
    min-width: 10rem;
    max-width: 14rem;
    padding: 0.35rem 0.5rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .mono {
    font-family: var(--mono);
    padding: 0.35rem 0.5rem;
  }

  .grid-cell input {
    width: 100%;
    min-width: 7rem;
    border: none;
    padding: 0.35rem 0.5rem;
    font: inherit;
    background: transparent;
  }

  .grid-cell.date-col input,
  input.date-input {
    min-width: 2.75rem;
    max-width: 4rem;
    text-align: center;
    font-family: var(--mono);
  }

  .edit-grid th.date-col {
    min-width: 2.75rem;
  }

  .grid-cell input:focus {
    outline: 2px solid var(--accent);
    outline-offset: -2px;
  }

  .grid-cell.amended input {
    background: #eef6fa;
  }

  .grid-cell.dirty input {
    background: #fff8e6;
  }

  .grid-toolbar label input {
    max-width: none;
  }
</style>
