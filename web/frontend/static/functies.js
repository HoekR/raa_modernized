const periodSelect = document.getElementById("period");
const searchForm = document.getElementById("search-form");
const resultsBody = document.querySelector("#results tbody");
const resultCount = document.getElementById("result-count");
const detailSection = document.getElementById("detail");
const detailBody = document.getElementById("detail-body");
const searchPanel = document.querySelector(".search-panel");
const resultsSection = document.querySelector("main > section:nth-of-type(2)");
const pagerTop = document.getElementById("pager");
const pagerBottom = document.getElementById("pager-bottom");

let searchOffset = 0;

const azBrowser = createAzBrowser("az-browser", "functies", periodSelect, {
  onSelect: () => {
    searchForm.q.value = "";
    searchOffset = 0;
    runSearch();
  },
  onClear: () => {
    searchOffset = 0;
    runSearch();
  },
});

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
  const letter = azBrowser.getLetter();
  const q = searchForm.q.value.trim();
  let data;
  if (letter && !q) {
    const params = new URLSearchParams({
      letter,
      from: String(searchOffset),
      size: String(PAGE_SIZE),
      period_mode: periodMode(periodSelect),
    });
    const period = periodValue(periodSelect);
    if (period) params.set("period", period);
    const res = await fetch(`/api/browse/functies/az?${params}`);
    data = await res.json();
  } else {
    const body = {
      q: q || null,
      period: periodValue(periodSelect),
      period_mode: periodMode(periodSelect),
      from: searchOffset,
      size: PAGE_SIZE,
    };
    const res = await fetch("/api/search/functies", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    data = await res.json();
  }
  resultCount.textContent = `${data.total} treffers`;
  renderPager(data.total);
  resultsBody.innerHTML = "";
  for (const row of data.hits) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${row.naam}</td><td>${row.aanstelling_count}</td>`;
    tr.addEventListener("click", () => showDetail(row.id));
    resultsBody.appendChild(tr);
  }
}

async function showDetail(id) {
  const res = await fetch(`/api/functies/${id}`);
  const item = await res.json();
  showEntityDetailView({ searchPanel, resultsSection, detailSection, detailBody });
  renderEntityProfile(detailBody, item.profile);
  history.replaceState(null, "", `?functie=${id}`);
}

document.getElementById("back-to-results").addEventListener("click", () => {
  hideEntityDetailView({ searchPanel, resultsSection, detailSection });
  history.replaceState(null, "", window.location.pathname);
});

searchForm.addEventListener("submit", (e) => {
  e.preventDefault();
  azBrowser.clear();
  searchOffset = 0;
  runSearch();
});

periodSelect.addEventListener("change", async () => {
  searchOffset = 0;
  await azBrowser.refreshCounts();
  runSearch();
});

const deepLinkFunctie = new URLSearchParams(window.location.search).get("functie");
loadPeriods(periodSelect, "functies").then(async () => {
  await azBrowser.refreshCounts();
  if (deepLinkFunctie) {
    showDetail(Number(deepLinkFunctie));
  } else {
    runSearch();
  }
});
