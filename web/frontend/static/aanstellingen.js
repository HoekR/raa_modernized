const periodSelect = document.getElementById("period");
const searchForm = document.getElementById("search-form");
const resultsBody = document.querySelector("#results tbody");
const resultsHeader = document.getElementById("results-header");
const resultCount = document.getElementById("result-count");
const facetsEl = document.getElementById("facets");

const functiePicker = createChipPicker(
  "functie-input", "functie-suggest", "functie-chips", "functie", "functie_id", periodSelect
);
const instellingPicker = createChipPicker(
  "instelling-input", "instelling-suggest", "instelling-chips", "instelling", "instelling_id", periodSelect
);
const provinciePicker = createGeoPicker("provincie-input", "provincie-suggest", "provincie-chips", "provincie", periodSelect);
const regioPicker = createGeoPicker("regio-input", "regio-suggest", "regio-chips", "regio", periodSelect);
const lokaalPicker = createGeoPicker("lokaal-input", "lokaal-suggest", "lokaal-chips", "lokaal", periodSelect);

function setHeaders(groupBy) {
  resultsHeader.innerHTML = "";
  const cols = groupBy
    ? ["Naam", "Aantal"]
    : ["Persoon", "Functie", "Instelling", "Van", "Tot"];
  for (const col of cols) {
    const th = document.createElement("th");
    th.textContent = col;
    resultsHeader.appendChild(th);
  }
}

async function runSearch() {
  const filters = {};
  functiePicker.addToFilters(filters);
  instellingPicker.addToFilters(filters);
  if (searchForm.van.value) filters.van = [searchForm.van.value];
  if (searchForm.tot.value) filters.tot = [searchForm.tot.value];
  provinciePicker.addGeoFilters(filters);
  regioPicker.addGeoFilters(filters);
  lokaalPicker.addGeoFilters(filters);

  const groupBy = searchForm.group_by.value || null;
  setHeaders(groupBy);

  const body = {
    q: searchForm.q.value.trim() || null,
    period: periodValue(periodSelect),
    period_mode: periodMode(periodSelect),
    filters,
    from: 0,
    size: 20,
    group_by: groupBy,
  };
  const res = await fetch("/api/search/aanstellingen", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  resultCount.textContent = `${data.total} treffers`;
  renderFacets(facetsEl, data.facets);
  resultsBody.innerHTML = "";

  for (const row of data.hits) {
    const tr = document.createElement("tr");
    if (groupBy) {
      tr.innerHTML = `<td>${row.naam}</td><td>${row.count}</td>`;
    } else {
      tr.innerHTML = `<td>${personName(row)}</td><td>${row.functie || "-"}</td><td>${row.instelling || "-"}</td><td>${row.van_als_bekend || "-"}</td><td>${row.tot_als_bekend || "-"}</td>`;
      tr.addEventListener("click", () => {
        window.location.href = personDetailUrl(row.persoon_id);
      });
    }
    resultsBody.appendChild(tr);
  }
}

searchForm.addEventListener("submit", (e) => {
  e.preventDefault();
  runSearch();
});

periodSelect.addEventListener("change", runSearch);
loadPeriods(periodSelect, "aanstellingen").then(() => {
  setHeaders(null);
  runSearch();
});
