<script lang="ts">
  import '../app.css';
  import { page } from '$app/stores';
  import PeriodSelect from '$lib/components/PeriodSelect.svelte';
  import { loadPeriods } from '$lib/search';
  import { periodKey, type PeriodCount } from '$lib/period';
  import { THEME_OPTIONS, colorTheme, type ColorTheme } from '$lib/theme';

  let { children } = $props();

  let periods = $state<PeriodCount[]>([]);

  const nav = [
    { href: '/personen', label: 'Personen' },
    { href: '/aanstellingen', label: 'Aanstellingen' },
    { href: '/instellingen', label: 'Instellingen' },
    { href: '/functies', label: 'Functies' },
  ];

  async function refreshPeriods(context: string) {
    try {
      periods = await loadPeriods(context);
      const current = $periodKey;
      if (current !== 'all' && periods.length && !periods.some((p) => p.key === current)) {
        periodKey.set(periods[0].key);
      } else if (!current && periods.length) {
        periodKey.set(periods[0].key);
      }
    } catch {
      periods = [];
    }
  }

  $effect(() => {
    const path = $page.url.pathname;
    let context = 'personen';
    if (path.startsWith('/aanstellingen')) context = 'aanstellingen';
    else if (path.startsWith('/instellingen')) context = 'instellingen';
    else if (path.startsWith('/functies')) context = 'functies';
    refreshPeriods(context);
  });
</script>

<header class="site-header">
  <div class="site-header-inner">
    <div class="brand-block">
      <p class="eyebrow">Huygens Instituut · repertorium</p>
      <a class="brand" href="/">
        <span class="brand-mark" aria-hidden="true"></span>
        <span class="brand-text">
          <span class="brand-title">RAA</span>
          <span class="brand-sub">Ambtenaren &amp; Ambtsdragers 1428–1861</span>
        </span>
      </a>
      <nav class="main-nav" aria-label="Zoekcontext">
        {#each nav as item}
          <a href={item.href} class:active={$page.url.pathname.startsWith(item.href)}>{item.label}</a>
        {/each}
      </nav>
    </div>
    <PeriodSelect {periods} />
  </div>
</header>

<div class="pilot-bar">
  <div class="pilot-inner">
    <p class="pilot-note">
      Pilot: <a href="http://127.0.0.1:8000/static/index.html">/static/</a>
    </p>
    <label class="theme-pick">
      Kleuren
      <select
        value={$colorTheme}
        onchange={(e) => colorTheme.set((e.currentTarget as HTMLSelectElement).value as ColorTheme)}
      >
        {#each THEME_OPTIONS as opt}
          <option value={opt.id}>{opt.label}</option>
        {/each}
      </select>
    </label>
  </div>
</div>

<main class="site-main">
  {@render children()}
</main>

<style>
  .site-header {
    background: var(--raa-ink);
    color: #f5f5f5;
    border-bottom: 3px solid var(--raa-accent-bright);
  }

  .site-header-inner {
    max-width: var(--raa-max);
    margin: 0 auto;
    padding: 1.1rem 1.5rem 1.25rem;
    display: flex;
    justify-content: space-between;
    gap: 1.5rem;
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .eyebrow {
    margin: 0 0 0.45rem;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--raa-accent-bright);
  }

  .brand {
    display: flex;
    gap: 0.75rem;
    align-items: center;
    text-decoration: none;
    color: inherit;
  }

  .brand:hover {
    color: #fff;
  }

  .brand-mark {
    width: 0.55rem;
    height: 2.4rem;
    background: var(--raa-accent-bright);
    flex-shrink: 0;
  }

  .brand-text {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
  }

  .brand-title {
    font-size: 1.65rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 1;
  }

  .brand-sub {
    font-size: 0.85rem;
    color: #cfcfcf;
    font-weight: 400;
  }

  .main-nav {
    display: flex;
    flex-wrap: wrap;
    gap: 0.15rem 0.35rem;
    margin-top: 1rem;
  }

  .main-nav a {
    color: #d6d6d6;
    text-decoration: none;
    padding: 0.35rem 0.7rem;
    border-radius: var(--raa-radius);
    font-size: 0.92rem;
    font-weight: 500;
    transition:
      background var(--raa-ease),
      color var(--raa-ease);
  }

  .main-nav a:hover {
    color: #fff;
    background: rgb(255 255 255 / 0.08);
  }

  .main-nav a.active {
    color: var(--raa-ink);
    background: var(--raa-accent-bright);
    font-weight: 600;
  }

  .pilot-bar {
    border-bottom: 1px solid var(--raa-line);
    background: var(--raa-accent-softer);
  }

  .pilot-inner {
    max-width: var(--raa-max-detail);
    margin: 0 auto;
    padding: 0.25rem 1.5rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem 1.5rem;
    align-items: center;
    justify-content: space-between;
  }

  .pilot-note {
    margin: 0;
    font-size: 0.72rem;
    color: var(--raa-ink-faint);
  }

  .pilot-inner p {
    margin: 0;
    font-size: 0.8rem;
    color: var(--raa-ink-muted);
  }

  .theme-pick {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 0.45rem;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--raa-ink-muted);
  }

  .theme-pick select {
    text-transform: none;
    letter-spacing: normal;
    font-weight: 500;
    font-size: 0.8rem;
    padding: 0.25rem 0.4rem;
    min-width: auto;
  }

  .site-main {
    max-width: var(--raa-max);
    margin: 0 auto;
    padding: 1.5rem 1.5rem 3.5rem;
  }

  :global(.site-main:has(.detail-route)) {
    max-width: var(--raa-max-detail);
  }

  :global(.site-header .period-select) {
    color: #f0f0f0;
  }

  :global(.site-header .period-select select) {
    background: var(--raa-header-elevated);
    color: #fff;
    border-color: #5a6a74;
    min-width: 14rem;
  }

  :global(.site-header .period-select select:focus) {
    border-color: var(--raa-accent-bright);
  }
</style>
