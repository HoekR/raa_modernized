const periodSelect = document.getElementById("period");
const searchForm = document.getElementById("search-form");
const resultsBody = document.querySelector("#results tbody");
const resultCount = document.getElementById("result-count");
const facetsEl = document.getElementById("facets");
const detailSection = document.getElementById("detail");
const searchPanel = document.querySelector(".search-panel");
const resultsSection = document.querySelector("main > section:nth-of-type(2)");

let functieId = null;
let instellingId = null;

const provinciePicker = createGeoPicker("provincie-input", "provincie-suggest", "provincie-chips", "provincie", periodSelect);
const regioPicker = createGeoPicker("regio-input", "regio-suggest", "regio-chips", "regio", periodSelect);
const lokaalPicker = createGeoPicker("lokaal-input", "lokaal-suggest", "lokaal-chips", "lokaal", periodSelect);

wireSuggest(
  document.getElementById("functie-input"),
  document.getElementById("functie-suggest"),
  "functie",
  periodSelect,
  (item) => { functieId = item.id; document.getElementById("functie-input").value = item.naam; }
);
wireSuggest(
  document.getElementById("instelling-input"),
  document.getElementById("instelling-suggest"),
  "instelling",
  periodSelect,
  (item) => { instellingId = item.id; document.getElementById("instelling-input").value = item.naam; }
);

document.getElementById("functie-input").addEventListener("input", (e) => {
  if (!e.target.value) functieId = null;
});
document.getElementById("instelling-input").addEventListener("input", (e) => {
  if (!e.target.value) instellingId = null;
});

function buildFilters() {
  const filters = {};
  if (functieId) filters.functie_id = [String(functieId)];
  if (instellingId) filters.instelling_id = [String(instellingId)];
  provinciePicker.addGeoFilters(filters);
  regioPicker.addGeoFilters(filters);
  lokaalPicker.addGeoFilters(filters);
  return filters;
}

async function runSearch() {
  const q = searchForm.q.value.trim();
  const body = {
    q: q || null,
    period: periodValue(periodSelect),
    period_mode: periodMode(periodSelect),
    filters: buildFilters(),
    from: 0,
    size: 20,
    sort: "geslachtsnaam",
  };
  const res = await fetch("/api/search/personen", {
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
    tr.innerHTML = `<td>${personName(row)}</td><td>${row.geboortedatum_als_bekend || "-"}</td><td>${row.overlijdensdatum_als_bekend || "-"}</td>`;
    tr.addEventListener("click", () => showDetail(row.id));
    resultsBody.appendChild(tr);
  }
}

async function showDetail(id) {
  const res = await fetch(`/api/personen/${id}`);
  const p = await res.json();
  searchPanel.hidden = true;
  resultsSection.hidden = true;
  detailSection.hidden = false;
  document.getElementById("detail-name").textContent = personName(p);
  document.getElementById("detail-dates").textContent = `Geboren: ${p.geboortedatum_als_bekend || "-"} — Overleden: ${p.overlijdensdatum_als_bekend || "-"}`;
  const aliases = document.getElementById("detail-aliases");
  aliases.innerHTML = "";
  for (const a of p.aliassen || []) {
    const li = document.createElement("li");
    li.textContent = a.naam;
    aliases.appendChild(li);
  }
  const aanst = document.getElementById("detail-aanstellingen");
  aanst.innerHTML = "";
  for (const a of p.aanstellingen || []) {
    const li = document.createElement("li");
    li.textContent = `${a.functie || "?"} — ${a.instelling || "?"} (${a.van_als_bekend || "?"} – ${a.tot_als_bekend || "?"})`;
    aanst.appendChild(li);
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
  runSearch();
});

periodSelect.addEventListener("change", runSearch);

const deepLinkPerson = new URLSearchParams(window.location.search).get("person");
loadPeriods(periodSelect, "personen").then(() => {
  if (deepLinkPerson) {
    showDetail(Number(deepLinkPerson));
  } else {
    runSearch();
  }
});
