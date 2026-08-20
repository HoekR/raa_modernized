import { base } from '$app/paths';

/** Path inside the admin app. Respects `ADMIN_BASE_PATH` (e.g. `/redactie`). */
export function appPath(path: string = '/'): string {
  const normalized = path.startsWith('/') ? path : `/${path}`;
  if (normalized === '/') return base || '/';
  return `${base}${normalized}`;
}
