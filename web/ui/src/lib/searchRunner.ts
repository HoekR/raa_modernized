/**
 * Ignore stale async search responses when a newer runSearch started later
 * (e.g. period effect vs wildcard submit racing).
 */
export class SearchRunGuard {
  #generation = 0;

  /** Call at the start of each search; pass token through to isCurrent. */
  begin(): number {
    return ++this.#generation;
  }

  isCurrent(token: number): boolean {
    return token === this.#generation;
  }
}
