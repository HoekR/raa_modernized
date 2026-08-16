const periodSelect = document.getElementById("period");
const searchForm = document.getElementById("search-form");
const resultsTable = document.getElementById("results");
const resultsBody = document.querySelector("#results tbody");
const resultCount = document.getElementById("result-count");
const facetsEl = document.getElementById("facets");
const pagerTop = document.getElementById("pager");
const pagerBottom = document.getElementById("pager-bottom");
const detailSection = document.getElementById("detail");
const searchPanel = document.querySelector(".search-panel");
const resultsSection = document.querySelector("main > section:nth-of-type(2)");

let searchOffset = 0;
let currentSort = "geslachtsnaam";

const functiePicker = createChipPicker(
  "functie-input", "functie-suggest", "functie-chips", "functie", "functie_id", periodSelect
);
const instellingPicker = createChipPicker(
  "instelling-input", "instelling-suggest", "instelling-chips", "instelling", "instelling_id", periodSelect
);
const provinciePicker = createGeoPicker("provincie-input", "provincie-suggest", "provincie-chips", "provincie", periodSelect);
const regioPicker = createGeoPicker("regio-input", "regio-suggest", "regio-chips", "regio", periodSelect);
const lokaalPicker = createGeoPicker("lokaal-input", "lokaal-suggest", "lokaal-chips", "lokaal", periodSelect);
const standFilter = createStandFilter("stand-filters");

function buildFilters() {
  const filters = {};
  functiePicker.addToFilters(filters);
  instellingPicker.addToFilters(filters);
  provinciePicker.addGeoFilters(filters);
  regioPicker.addGeoFilters(filters);
  lokaalPicker.addGeoFilters(filters);
  standFilter.addToFilters(filters);
  addAdelFilter(searchForm, filters);
  const geboorte = searchForm.geboorte.value.trim();
  const overlijden = searchForm.overlijden.value.trim();
  if (geboorte) filters.geboorte = [geboorte];
  if (overlijden) filters.overlijden = [overlijden];
  const van = searchForm.van.value.trim();
  const tot = searchForm.tot.value.trim();
  if (van) filters.van = [van];
  if (tot) filters.tot = [tot];
  return filters;
}

function renderPager(total) {
  const opts = {
    total,
    offset: searchOffset,
    pageSize: PAGE_SIZE,
    onPageChange: (offset) => {
      searchOffset = offset;
      runSearch();
    },
  };
  renderPagination(pagerTop, opts);
  renderPagination(pagerBottom, opts);
}

async function runSearch() {
  const q = searchForm.q.value.trim();
  const body = {
    q: q || null,
    period: periodValue(periodSelect),
    period_mode: periodMode(periodSelect),
    filters: buildFilters(),
    functie_match: matchModeValue(searchForm, "functie"),
    instelling_match: matchModeValue(searchForm, "instelling"),
    include_shadow_dates: includeShadowDates(searchForm),
    from: searchOffset,
    size: PAGE_SIZE,
    sort: currentSort,
  };
  const res = await fetch("/api/search/personen", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  resultCount.textContent = `${data.total} treffers`;
  renderFacets(facetsEl, data.facets);
  renderPager(data.total);
  updateSortableHeaders(resultsTable, currentSort);
  resultsBody.innerHTML = "";
  for (const row of data.hits) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${listingPersonName(row)}</td><td>${formatLifeDateCell(row, "geboorte")}</td><td>${formatLifeDateCell(row, "overlijden")}</td>`;
    tr.addEventListener("click", () => showDetail(row.id));
    resultsBody.appendChild(tr);
  }
}

function resetSearch() {
  searchOffset = 0;
  runSearch();
}

function setSectionVisible(section, visible) {
  section.hidden = !visible;
}

function renderAliases(container, aliases) {
  container.innerHTML = "";
  if (!aliases?.length) return false;
  for (const a of aliases) {
    const li = document.createElement("li");
    li.textContent = a.naam;
    container.appendChild(li);
  }
  return true;
}

function renderBronnen(container, bronnen) {
  container.innerHTML = "";
  if (!bronnen?.length) return false;
  for (const b of bronnen) {
    const p = document.createElement("p");
    p.className = "bron-item";
    const details = b.details ? ` ${b.details}` : "";
    p.textContent = `${b.naam}${details}`;
    container.appendChild(p);
  }
  return true;
}

function renderLokaalAanstelling(a) {
  const li = document.createElement("li");
  let text = `${a.functie || "?"} ${a.instelling || ""} (${a.van_als_bekend || "?"} – ${a.tot_als_bekend || "?"})`;
  if (a.opmerkingen) text += ` — ${a.opmerkingen}`;
  li.textContent = text;
  return li;
}

function renderBovenlokaalAanstelling(a) {
  const block = document.createElement("div");
  block.className = "aanstelling-block";
  const lines = [];
  lines.push(`<strong>functie:</strong> ${escapeHtml(a.functie || "?")}`);
  if (a.instelling) {
    lines.push(
      `<strong>instelling:</strong> <a href="/static/instellingen.html?instelling=${a.instelling_id}">${escapeHtml(a.instelling)}</a>`
    );
  }
  lines.push(`<strong>van:</strong> ${escapeHtml(a.van_als_bekend || "?")} – ${escapeHtml(a.tot_als_bekend || "?")}`);
  const namens = formatNamens(a);
  if (namens) {
    lines.push(`<strong>namens:</strong> ${escapeHtml(namens)}`);
  }
  const link = aanstellingSearchUrl({ functieId: a.functie_id, instellingId: a.instelling_id });
  lines.push(`<a href="${link}">anderen met deze aanstelling…</a>`);
  if (a.opmerkingen_html) {
    lines.push(`<p class="opmerkingen">${a.opmerkingen_html}</p>`);
  } else if (a.opmerkingen) {
    lines.push(`<p class="opmerkingen">${escapeHtml(a.opmerkingen)}</p>`);
  }
  block.innerHTML = lines.join("<br />");
  return block;
}

async function showDetail(id) {
  const res = await fetch(`/api/personen/${id}`);
  const p = await res.json();
  searchPanel.hidden = true;
  resultsSection.hidden = true;
  detailSection.hidden = false;

  document.getElementById("detail-name").textContent = p.display_naam || personName(p);
  const heer = document.getElementById("detail-heerlijkheid");
  if (p.heerlijkheid_line) {
    heer.textContent = p.heerlijkheid_line;
    heer.hidden = false;
  } else {
    heer.hidden = true;
  }

  const aliasesBlock = document.getElementById("detail-aliases-block");
  setSectionVisible(aliasesBlock, renderAliases(document.getElementById("detail-aliases"), p.aliassen));

  const life = p.life_summary || {};
  document.getElementById("detail-dates").innerHTML = [
    life.geboorte
      ? `${life.geboorte}${lifeDateBadges(p, "geboorte")}`
      : formatLifeDateLine("geboren", p, "geboorte"),
    life.overlijden
      ? `${life.overlijden}${lifeDateBadges(p, "overlijden")}`
      : formatLifeDateLine("overleden", p, "overlijden"),
  ].join("<br />");

  const opmBlock = document.getElementById("detail-opmerkingen-block");
  const opmEl = document.getElementById("detail-opmerkingen");
  if (p.opmerkingen_html) {
    opmEl.innerHTML = p.opmerkingen_html;
    setSectionVisible(opmBlock, true);
  } else {
    setSectionVisible(opmBlock, false);
  }

  const bronBlock = document.getElementById("detail-bronnen-block");
  setSectionVisible(bronBlock, renderBronnen(document.getElementById("detail-bronnen"), p.bronnen));

  const lokaal = p.aanstellingen_lokaal || [];
  const lokaalSection = document.getElementById("detail-lokaal-section");
  const lokaalList = document.getElementById("detail-aanstellingen-lokaal");
  lokaalList.innerHTML = "";
  if (lokaal.length) {
    setSectionVisible(lokaalSection, true);
    for (const a of lokaal) {
      lokaalList.appendChild(renderLokaalAanstelling(a));
    }
  } else {
    setSectionVisible(lokaalSection, false);
  }

  const bovenlokaal = document.getElementById("detail-aanstellingen-bovenlokaal");
  bovenlokaal.innerHTML = "";
  const boven = p.aanstellingen_bovenlokaal || [];
  if (!boven.length) {
    bovenlokaal.innerHTML = "<p><em>Geen bovenlokale aanstellingen</em></p>";
  } else {
    for (const a of boven) {
      bovenlokaal.appendChild(renderBovenlokaalAanstelling(a));
    }
  }

  history.replaceState(null, "", `?person=${id}`);
}

document.getElementById("back-to-results").addEventListener("click", () => {
  detailSection.hidden = true;
  searchPanel.hidden = false;
  resultsSection.hidden = false;
  history.replaceState(null, "", window.location.pathname);
});

searchForm.addEventListener("submit", (e) => {
  e.preventDefault();
  resetSearch();
});

periodSelect.addEventListener("change", resetSearch);

wireSortableHeaders(
  resultsTable,
  () => currentSort,
  (sort) => {
    currentSort = sort;
    searchOffset = 0;
  },
  resetSearch
);

async function applyDeepLinkFilters() {
  const params = new URLSearchParams(window.location.search);
  const functieId = params.get("functie_id");
  if (functieId) {
    const item = await fetchEntityName("functies", functieId);
    if (item) functiePicker.seed(item);
  }
}

const deepLinkPerson = new URLSearchParams(window.location.search).get("person");
loadPeriods(periodSelect, "personen").then(async () => {
  await standFilter.prepare();
  await applyDeepLinkFilters();
  if (deepLinkPerson) {
    showDetail(Number(deepLinkPerson));
  } else {
    runSearch();
  }
});
