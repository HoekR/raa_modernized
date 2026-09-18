/** Hybrid list URL history: replace while refining; push when settled (RS D2). */

import { pushState, replaceState } from '$app/navigation';

const SETTLE_MS = 600;
let lastPushAt = 0;
let lastPath = '';

export function commitListUrl(path: string, opts?: { forcePush?: boolean }) {
  if (path === lastPath && !opts?.forcePush) {
    replaceState(path, {});
    return;
  }
  const now = Date.now();
  const settled = now - lastPushAt >= SETTLE_MS;
  if (opts?.forcePush || settled || !lastPath) {
    pushState(path, {});
    lastPushAt = now;
  } else {
    replaceState(path, {});
  }
  lastPath = path;
}

export function resetListHistory() {
  lastPushAt = 0;
  lastPath = '';
}
