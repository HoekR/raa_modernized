const periodSelect = document.getElementById("period");
const searchForm = document.getElementById("search-form");
const resultsBody = document.querySelector("#results tbody");
const resultCount = document.getElementById("result-count");
const detailSection = document.getElementById("detail");
const searchPanel = document.querySelector(".search-panel");
const resultsSection = document.querySelector("main > section:nth-of-type(2)");

async function runSearch() {
  const body = {
    q: searchForm.q.value.trim() || null,
    period: periodValue(periodSelect),
    period_mode: periodMode(periodSelect),
    from: 0,
    size: 20,
  };
  const res = await fetch("/api/search/instellingen", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  resultCount.textContent = `${data.total} treffers`;
  resultsBody.innerHTML = "";
  for (const row of data.hits) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${row.naam}</td><td>${row.aanstelling_count}</td>`;
    tr.addEventListener("click", () => showDetail(row.id));
    resultsBody.appendChild(tr);
  }
}

async function showDetail(id) {
  const res = await fetch(`/api/instellingen/${id}`);
  const item = await res.json();
  searchPanel.hidden = true;
  resultsSection.hidden = true;
  detailSection.hidden = false;
  document.getElementById("detail-name").textContent = item.naam;
  document.getElementById("detail-count").textContent = `${item.aanstelling_count} aanstellingen`;
  const toel = document.getElementById("detail-toelichting");
  toel.innerHTML = item.toelichting || "<em>Geen toelichting</em>";
}

document.getElementById("back-to-results").addEventListener("click", () => {
  detailSection.hidden = true;
  searchPanel.hidden = false;
  resultsSection.hidden = false;
});

searchForm.addEventListener("submit", (e) => {
  e.preventDefault();
  runSearch();
});

periodSelect.addEventListener("change", runSearch);
loadPeriods(periodSelect, "instellingen").then(runSearch);
