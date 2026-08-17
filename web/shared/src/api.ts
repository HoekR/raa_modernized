/** Shared fetch helpers for RAA public + admin apps. */

export type ApiFetchOptions = {
  apiKey?: string;
  method?: string;
  body?: unknown;
};

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const headers: Record<string, string> = {};
  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }
  if (options.apiKey) {
    headers['X-Editorial-Api-Key'] = options.apiKey;
  }
  const res = await fetch(path, {
    method: options.method ?? (options.body !== undefined ? 'POST' : 'GET'),
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`${path} → ${res.status}${text ? `: ${text}` : ''}`);
  }
  return res.json() as Promise<T>;
}

export async function apiGet<T>(path: string, apiKey?: string): Promise<T> {
  return apiFetch<T>(path, { apiKey });
}

export async function apiPost<T>(path: string, body: unknown, apiKey?: string): Promise<T> {
  return apiFetch<T>(path, { method: 'POST', body, apiKey });
}

export async function apiDelete<T>(path: string, apiKey?: string): Promise<T> {
  return apiFetch<T>(path, { method: 'DELETE', apiKey });
}

export async function apiDownload(path: string, filename: string, apiKey?: string): Promise<void> {
  const headers: Record<string, string> = {};
  if (apiKey) {
    headers['X-Editorial-Api-Key'] = apiKey;
  }
  const res = await fetch(path, { headers });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`${path} → ${res.status}${text ? `: ${text}` : ''}`);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export async function apiUpload<T>(
  path: string,
  file: File,
  apiKey?: string,
  params?: Record<string, string>
): Promise<T> {
  const url = params
    ? `${path}?${new URLSearchParams(params).toString()}`
    : path;
  const headers: Record<string, string> = {};
  if (apiKey) {
    headers['X-Editorial-Api-Key'] = apiKey;
  }
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(url, { method: 'POST', headers, body: form });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`${url} → ${res.status}${text ? `: ${text}` : ''}`);
  }
  return res.json() as Promise<T>;
}
