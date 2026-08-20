const periodSelect = document.getElementById("period");
const searchForm = document.getElementById("search-form");
const resultsNested = document.getElementById("results-nested");
const resultCount = document.getElementById("result-count");
const facetsEl = document.getElementById("facets");
const pagerTop = document.getElementById("pager");
const pagerBottom = document.getElementById("pager-bottom");

let searchOffset = 0;

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
  if (searchForm.van.value.trim()) filters.van = [searchForm.van.value.trim()];
  if (searchForm.tot.value.trim()) filters.tot = [searchForm.tot.value.trim()];
  provinciePicker.addGeoFilters(filters);
  regioPicker.addGeoFilters(filters);
  lokaalPicker.addGeoFilters(filters);
  standFilter.addToFilters(filters);
  addAdelFilter(searchForm, filters);
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

function renderNestedResults(hits, groupBy) {
  resultsNested.innerHTML = "";
  if (!hits.length) {
    resultsNested.innerHTML = "<p><em>Geen treffers</em></p>";
    return;
  }

  const outerKey = groupBy === "functie" ? "functie" : "instelling";
  const innerKey = groupBy === "functie" ? "instelling" : "functie";
  const groups = groupNestedHits(hits, outerKey, innerKey);

  for (const outer of groups) {
    const outerEl = document.createElement("section");
    outerEl.className = "group-outer";
    const outerTitle = document.createElement("h3");
    outerTitle.textContent = outer.naam || "(onbekend)";
    outerEl.appendChild(outerTitle);

    for (const inner of outer.inner) {
      const innerEl = document.createElement("div");
      innerEl.className = "group-inner";
      const innerTitle = document.createElement("h4");
      innerTitle.textContent = inner.naam || "(onbekend)";
      innerEl.appendChild(innerTitle);

      const list = document.createElement("ul");
      list.className = "person-rows";
      for (const row of inner.rows) {
        const li = document.createElement("li");
        const link = document.createElement("a");
        link.href = personDetailUrl(row.persoon_id);
        link.textContent = personName(row);
        li.append(
          link,
          document.createTextNode(
            ` (${row.van_als_bekend || "?"} – ${row.tot_als_bekend || "?"})`
          )
        );
        list.appendChild(li);
      }
      innerEl.appendChild(list);
      outerEl.appendChild(innerEl);
    }
    resultsNested.appendChild(outerEl);
  }
}

async function runSearch() {
  const groupBy = searchForm.group_by.value || "instelling";
  const body = {
    q: searchForm.q.value.trim() || null,
    period: periodValue(periodSelect),
    period_mode: periodMode(periodSelect),
    filters: buildFilters(),
    functie_match: matchModeValue(searchForm, "functie"),
    instelling_match: matchModeValue(searchForm, "instelling"),
    from: searchOffset,
    size: PAGE_SIZE,
    sort: searchForm.sort.value || "van",
    group_by: null,
  };
  const res = await fetch("/api/search/aanstellingen", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  resultCount.textContent = `${data.total} treffers`;
  renderFacets(facetsEl, data.facets);
  renderPager(data.total);
  renderNestedResults(data.hits, groupBy);
}

function resetSearch() {
  searchOffset = 0;
  runSearch();
}

searchForm.addEventListener("submit", (e) => {
  e.preventDefault();
  resetSearch();
});

periodSelect.addEventListener("change", resetSearch);

const params = new URLSearchParams(window.location.search);

async function applyDeepLinkFilters() {
  const functieId = params.get("functie_id");
  const instellingId = params.get("instelling_id");
  if (functieId) {
    const item = await fetchEntityName("functies", functieId);
    if (item) functiePicker.seed(item);
  }
  if (instellingId) {
    const item = await fetchEntityName("instellingen", instellingId);
    if (item) instellingPicker.seed(item);
  }
}

loadPeriods(periodSelect, "aanstellingen").then(async () => {
  await standFilter.prepare();
  await applyDeepLinkFilters();
  runSearch();
});
