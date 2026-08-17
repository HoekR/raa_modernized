import { apiGet } from './api';

export type LifeSummary = { geboorte?: string; overlijden?: string };

export type AanstellingDetail = {
  id?: number;
  functie?: string;
  functie_id?: number;
  instelling?: string;
  instelling_id?: number;
  van_als_bekend?: string;
  tot_als_bekend?: string;
  provincie?: string;
  regio?: string;
  lokaal?: string;
  stand?: string;
  opmerkingen?: string;
  opmerkingen_html?: string;
  vertegenwoordigend?: boolean;
};

export type PersoonDetail = Record<string, unknown> & {
  id: number;
  display_naam?: string;
  heerlijkheid_line?: string;
  life_summary?: LifeSummary;
  aliassen?: { naam: string }[];
  bronnen?: { naam: string; details?: string }[];
  aanstellingen_lokaal?: AanstellingDetail[];
  aanstellingen_bovenlokaal?: AanstellingDetail[];
  opmerkingen_html?: string;
};

export type EntityStat = { label: string; value?: string | number; html?: string };

export type EntityProfile = {
  entity_type: string;
  id: number;
  naam: string;
  stats?: EntityStat[];
  actions?: { label: string; href: string }[];
  sections?: { title: string; html?: string; text?: string }[];
  related?: {
    title: string;
    items: {
      id?: number;
      naam: string;
      href?: string;
      aanstelling_count?: number;
      meta?: string;
    }[];
  }[];
};

/** Rewrite legacy /static/… links from the API into SvelteKit routes. */
export function modernizeHtml(html: string): string {
  return html
    .replace(/\/static\/instellingen\.html\?instelling=(\d+(?:\.\d+)?)/g, (_, id) => {
      return `/instellingen/${parseInt(id, 10)}`;
    })
    .replace(/\/static\/functies\.html\?functie=(\d+(?:\.\d+)?)/g, (_, id) => {
      return `/functies/${parseInt(id, 10)}`;
    })
    .replace(/\/static\/index\.html\?person=(\d+)/g, '/personen/$1')
    .replace(/\/static\/aanstellingen\.html\?/g, '/aanstellingen?');
}

export function modernizeHref(href: string | undefined): string {
  if (!href) return '#';
  return modernizeHtml(href);
}

export function formatNamens(a: AanstellingDetail): string {
  return [a.provincie, a.regio, a.lokaal, a.stand].filter(Boolean).join(' / ');
}

export async function fetchPersoon(id: number | string): Promise<PersoonDetail> {
  return apiGet(`/api/personen/${id}`);
}

export async function fetchInstelling(id: number | string): Promise<{
  id: number;
  naam: string;
  profile?: EntityProfile;
  aanstelling_count?: number;
}> {
  return apiGet(`/api/instellingen/${id}`);
}

export async function fetchFunctie(id: number | string): Promise<{
  id: number;
  naam: string;
  profile?: EntityProfile;
}> {
  return apiGet(`/api/functies/${id}`);
}
