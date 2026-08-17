import { describe, expect, it } from 'vitest';
import { SearchRunGuard } from './searchRunner';

describe('SearchRunGuard', () => {
  it('marks only the latest run as current', () => {
    const guard = new SearchRunGuard();
    const a = guard.begin();
    const b = guard.begin();
    expect(guard.isCurrent(a)).toBe(false);
    expect(guard.isCurrent(b)).toBe(true);
  });

  it('simulates stale response ignored after newer search', async () => {
    const guard = new SearchRunGuard();
    const results: string[] = [];

    async function runSearch(label: string, delayMs: number) {
      const token = guard.begin();
      await new Promise((r) => setTimeout(r, delayMs));
      if (!guard.isCurrent(token)) return;
      results.push(label);
    }

    await Promise.all([
      runSearch('empty-browse', 30),
      runSearch('wasse*', 5),
    ]);

    expect(results).toEqual(['wasse*']);
  });
});
