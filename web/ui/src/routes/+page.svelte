<section class="home">
  <div class="hero">
    <h1>Repertorium van Ambtenaren en Ambtsdragers</h1>
    <p class="lede">
      Zoek personen, aanstellingen, instellingen en functies in de periode 1428–1861.
      Kies een context; de periode rechtsboven geldt overal.
    </p>
  </div>

  <ul class="entry">
    <li>
      <a href="/personen">
        <span class="kicker">Zoeken</span>
        <strong>Personen</strong>
        <span class="desc">Naam, leven, facetten en filters</span>
      </a>
    </li>
    <li>
      <a href="/aanstellingen">
        <span class="kicker">Zoeken</span>
        <strong>Aanstellingen</strong>
        <span class="desc">Naam, facetten, geneste resultaten</span>
      </a>
    </li>
    <li>
      <a href="/instellingen">
        <span class="kicker">Bladeren</span>
        <strong>Instellingen</strong>
        <span class="desc">Zoeken, A–Z en detail</span>
      </a>
    </li>
    <li>
      <a href="/functies">
        <span class="kicker">Bladeren</span>
        <strong>Functies</strong>
        <span class="desc">Zoeken, A–Z en detail</span>
      </a>
    </li>
  </ul>
</section>

<style>
  .home {
    max-width: 40rem;
  }

  .hero {
    margin-bottom: 1.75rem;
  }

  h1 {
    font-size: clamp(1.75rem, 4vw, 2.35rem);
    margin: 0 0 0.75rem;
    letter-spacing: -0.03em;
  }

  .lede {
    font-size: 1.05rem;
    color: var(--raa-ink-muted);
    margin: 0;
    max-width: 34rem;
  }

  .entry {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 0.65rem;
  }

  .entry a {
    display: grid;
    gap: 0.15rem;
    text-decoration: none;
    background: var(--raa-surface);
    border: 1px solid var(--raa-line);
    border-left: 3px solid var(--raa-accent-bright);
    padding: 0.9rem 1rem;
    border-radius: var(--raa-radius);
    box-shadow: var(--raa-shadow);
    transition:
      border-color var(--raa-ease),
      transform var(--raa-ease),
      box-shadow var(--raa-ease);
  }

  .entry a:hover {
    border-color: var(--raa-accent);
    border-left-color: var(--raa-accent);
    transform: translateY(-1px);
    color: var(--raa-ink);
  }

  .kicker {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--raa-accent);
  }

  strong {
    font-size: 1.1rem;
  }

  .desc {
    font-size: 0.9rem;
    color: var(--raa-ink-muted);
  }
</style>
