import { apiDelete, apiDownload, apiGet, apiPost, apiUpload } from '@raa/shared';
import { getApiKey } from './auth';

export type AmendmentSummary = {
  id: number;
  editor_id: string;
  note: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  value?: string;
};

export type ToelichtingEditContext = {
  id: number;
  naam: string;
  toelichting_base: string | null;
  toelichting_effective: string | null;
  toelichting_amended: boolean;
  amendment: Record<string, unknown> | null;
  base_release_id: string | null;
  history: AmendmentSummary[];
  active_amendment: Record<string, unknown> | null;
};

export type FieldEditState = {
  base: unknown;
  effective: unknown;
  amended: boolean;
  amendment_id: number | null;
};

export type EntityEditContext = {
  entity_type: string;
  id: number;
  label: string;
  fields: Record<string, FieldEditState>;
};

export type ConflictRow = {
  id: number;
  amendment_id: number;
  entity_type: string;
  entity_id: number;
  field: string;
  old_base_value: string | null;
  new_base_value: string | null;
  amendment_value: string | null;
  release_id: string;
};

export function fetchEntityContext(entityType: string, id: string): Promise<EntityEditContext> {
  return apiGet<EntityEditContext>(
    `/api/editorial/${encodeURIComponent(entityType)}/${encodeURIComponent(id)}`,
    getApiKey()
  );
}

export function saveField(
  entityType: string,
  entityId: number,
  field: string,
  value: string,
  note?: string
) {
  return apiPost(
    '/api/editorial/amendments',
    { entity_type: entityType, entity_id: entityId, field, value, note: note || null },
    getApiKey()
  );
}

export function revertAmendment(amendmentId: number) {
  return apiDelete(`/api/editorial/amendments/${amendmentId}`, getApiKey());
}

export function fetchConflicts(): Promise<ConflictRow[]> {
  return apiGet<ConflictRow[]>('/api/editorial/conflicts', getApiKey());
}

export function resolveConflict(conflictId: number, resolution: 'keep_amendment' | 'accept_base') {
  return apiPost(`/api/editorial/conflicts/${conflictId}/resolve`, { resolution }, getApiKey());
}

export function fetchRecentAmendments() {
  return apiGet<Array<Record<string, unknown>>>(
    '/api/editorial/amendments?limit=20',
    getApiKey()
  );
}

// instelling toelichting (E1 dedicated endpoint)
export function fetchToelichtingContext(id: string): Promise<ToelichtingEditContext> {
  return apiGet<ToelichtingEditContext>(
    `/api/editorial/instellingen/${encodeURIComponent(id)}/toelichting`,
    getApiKey()
  );
}

export function saveToelichting(id: number, value: string, note?: string) {
  return saveField('instelling', id, 'toelichting', value, note);
}

export type GridFieldState = {
  base: string;
  effective: string;
  amended: boolean;
  amendment_id: number | null;
};

export type GridRow = {
  id: number;
  label: string;
  fields: Record<string, GridFieldState>;
};

export type GridColumnGroup = {
  label: string | null;
  fields: string[];
};

export type GridBatchResponse = {
  entity_type: string;
  fields: string[];
  rows: GridRow[];
  missing_ids: number[];
  column_groups?: GridColumnGroup[];
  field_labels?: Record<string, string>;
};

export type BatchChange = {
  entity_type: string;
  entity_id: number;
  field: string;
  value: string;
};

export type BatchResult = {
  applied: BatchChange[];
  reverted: BatchChange[];
  skipped: BatchChange[];
  errors: Array<BatchChange & { error: string }>;
};

export function fetchBatch(entityType: string, ids: number[]): Promise<GridBatchResponse> {
  const q = ids.join(',');
  return apiGet<GridBatchResponse>(
    `/api/editorial/batch/${encodeURIComponent(entityType)}?ids=${encodeURIComponent(q)}`,
    getApiKey()
  );
}

export function saveBatch(changes: BatchChange[], note?: string): Promise<BatchResult> {
  return apiPost<BatchResult>(
    '/api/editorial/amendments/batch',
    { changes, note: note || null },
    getApiKey()
  );
}

export const PERSOON_DATE_GROUPS: GridColumnGroup[] = [
  { label: 'geboorte', fields: ['geboortejaar', 'geboortemaand', 'geboortedag'] },
  { label: 'overlijden', fields: ['overlijdensjaar', 'overlijdensmaand', 'overlijdensdag'] },
];

export const DATE_PART_FIELDS = new Set([
  ...PERSOON_DATE_GROUPS[0].fields,
  ...PERSOON_DATE_GROUPS[1].fields,
]);

export function fieldHeader(field: string, labels?: Record<string, string>): string {
  return labels?.[field] ?? field;
}

export function isDatePartField(field: string): boolean {
  return DATE_PART_FIELDS.has(field);
}

/** Parse pasted or typed id lists (comma, newline, tab). */
export function parseIdList(raw: string): number[] {
  const parts = raw.split(/[\s,;]+/).map((p) => p.trim()).filter(Boolean);
  const ids: number[] = [];
  for (const part of parts) {
    const n = Number(part);
    if (Number.isInteger(n) && n > 0) ids.push(n);
  }
  return [...new Set(ids)];
}

export type ImportParseError = { row: number; column: string; error: string };

export type ImportResult = {
  rows_parsed: number;
  person_count?: number;
  change_count?: number;
  parse_errors: ImportParseError[];
  changes?: BatchChange[];
  dry_run: boolean;
  result: BatchResult | null;
};

const TEMPLATE_NAME = 'raa_persoon_werklijst.xlsx';

export function downloadPersoonTemplate(ids?: number[]) {
  const q =
    ids && ids.length
      ? `?ids=${encodeURIComponent(ids.join(','))}`
      : '';
  return apiDownload(
    `/api/editorial/import/persoon/template.xlsx${q}`,
    TEMPLATE_NAME,
    getApiKey()
  );
}

export function importPersoonFile(
  file: File,
  options?: { dryRun?: boolean; note?: string }
): Promise<ImportResult> {
  const params: Record<string, string> = {};
  if (options?.dryRun) params.dry_run = 'true';
  if (options?.note) params.note = options.note;
  return apiUpload<ImportResult>('/api/editorial/import/persoon', file, getApiKey(), params);
}
