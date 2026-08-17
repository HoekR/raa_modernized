<script lang="ts">
  import { modernizeHref, modernizeHtml, type EntityProfile } from '$lib/detail';

  const KICKERS: Record<string, string> = {
    persoon: 'Persoon',
    instelling: 'Instelling',
    functie: 'Functie',
  };

  let { profile }: { profile: EntityProfile } = $props();
</script>

<article class="detail">
  <header class="detail-hero">
    <p class="detail-kicker">{KICKERS[profile.entity_type] ?? profile.entity_type}</p>
    <h1>{profile.naam}</h1>
  </header>

  {#if profile.stats?.length}
    <dl class="detail-stats">
      {#each profile.stats as stat}
        <dt>{stat.label}</dt>
        <dd>
          {#if stat.html}
            {@html modernizeHtml(String(stat.html))}
          {:else}
            {stat.value}
          {/if}
        </dd>
      {/each}
    </dl>
  {/if}

  {#if profile.actions?.length}
    <nav class="detail-actions">
      {#each profile.actions as action}
        <a href={modernizeHref(action.href)}>{action.label}</a>
      {/each}
    </nav>
  {/if}

  {#each profile.sections || [] as section}
    {#if section.html || section.text}
      <section class="detail-section">
        <h2>{section.title}</h2>
        <div class="detail-prose">
          {#if section.html}
            {@html modernizeHtml(section.html)}
          {:else}
            <p>{section.text}</p>
          {/if}
        </div>
      </section>
    {/if}
  {/each}

  {#each profile.related || [] as group}
    {#if group.items?.length}
      <section class="detail-section">
        <h2>{group.title}</h2>
        <ul class="detail-related">
          {#each group.items as item}
            <li>
              <a href={modernizeHref(item.href)}>
                {item.naam}{#if item.aanstelling_count != null}
                  <span class="meta">({item.aanstelling_count})</span>{/if}{#if item.meta}
                  <span class="meta"> — {item.meta}</span>{/if}
              </a>
            </li>
          {/each}
        </ul>
      </section>
    {/if}
  {/each}
</article>
