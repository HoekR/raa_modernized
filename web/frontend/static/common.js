const MAX_CHIP_ITEMS = 5;
const PAGE_SIZE = 100;

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function periodMode(periodSelect) {
  return periodSelect.value === "all" ? "overall" : "scoped";
}

function periodValue(periodSelect) {
  return periodSelect.value === "all" ? null : periodSelect.value;
}

async function loadPeriods(periodSelect, context) {
  const res = await fetch(`/api/periods?context=${encodeURIComponent(context)}`);
  const periods = await res.json();
  periodSelect.innerHTML = "";
  for (const p of periods) {
    const opt = document.createElement("option");
    opt.value = p.key;
    opt.textContent = `${p.label} (${p.count})`;
    periodSelect.appendChild(opt);
  }
  const all = document.createElement("option");
  all.value = "all";
  all.textContent = "Alle perioden";
  periodSelect.appendChild(all);
  if (periods.length) periodSelect.value = periods[0].key;
}

function renderFacets(facetsEl, facets) {
  facetsEl.innerHTML = "";
  for (const [name, values] of Object.entries(facets || {})) {
    if (!values.length) continue;
    const group = document.createElement("div");
    group.className = "facet-group";
    group.innerHTML = `<strong>${name}</strong>`;
    const ul = document.createElement("ul");
    for (const v of values) {
      const li = document.createElement("li");
      li.textContent = `${v.label} (${v.count})`;
      ul.appendChild(li);
    }
    group.appendChild(ul);
    facetsEl.appendChild(group);
  }
}

function personName(row) {
  if (row.display_naam) return row.display_naam;
  return [row.voornaam, row.tussenvoegsel, row.geslachtsnaam].filter(Boolean).join(" ");
}

function listingPersonName(row) {
  if (row.listing_naam) return row.listing_naam;
  if (row.display_naam) return row.display_naam;
  const gs = row.geslachtsnaam?.trim();
  const vn = row.voornaam?.trim();
  const tv = row.tussenvoegsel?.trim();
  if (gs) return [vn, tv, gs].filter(Boolean).join(" ");
  return vn || personName(row);
}

function personDetailUrl(personId) {
  return `/static/index.html?person=${personId}`;
}

function aanstellingSearchUrl({ functieId = null, instellingId = null } = {}) {
  const params = new URLSearchParams();
  if (functieId) params.set("functie_id", String(functieId));
  if (instellingId) params.set("instelling_id", String(instellingId));
  const qs = params.toString();
  return `/static/aanstellingen.html${qs ? `?${qs}` : ""}`;
}

function formatNamens(a) {
  return [a.provincie, a.regio, a.lokaal, a.stand].filter(Boolean).join(", ");
}

function matchModeValue(form, field) {
  const selected = form.querySelector(`input[name="${field}_match"]:checked`);
  return selected ? selected.value : "any";
}

function includeShadowDates(form) {
  const exact = form.querySelector('input[name="date_mode"][value="exact"]');
  return !(exact && exact.checked);
}

function formatLifeDateCell(row, kind) {
  const isBirth = kind === "geboorte";
  const display = isBirth ? row.geboortedatum_als_bekend : row.overlijdensdatum_als_bekend;
  const edtf = isBirth ? row.geboorte_edtf : row.overlijden_edtf;
  const lifeYear = isBirth ? row.life_start_year : row.life_end_year;
  const lifeSource = isBirth ? row.life_start_source : row.life_end_source;

  let text = display != null ? String(display).trim() : "";
  if (!text) {
    if (lifeSource === "shadow" && lifeYear != null && lifeYear !== "") {
      return `${escapeHtml(String(lifeYear))} <span class="provenance geschat" title="Geschat uit aanstellingen">geschat</span>`;
    }
    return "-";
  }

  let html = escapeHtml(text);
  if (edtf && /[~?%]$/.test(String(edtf))) {
    html += ' <span class="provenance approx" title="Onzekere datum">~</span>';
  }
  if (lifeSource === "shadow" && !display) {
    html += ' <span class="provenance geschat" title="Geschat uit aanstellingen">geschat</span>';
  }
  return html;
}

function formatLifeDateLine(label, row, kind) {
  const cell = formatLifeDateCell(row, kind);
  return `${label}: ${cell}`;
}

function lifeDateBadges(row, kind) {
  const isBirth = kind === "geboorte";
  const edtf = isBirth ? row.geboorte_edtf : row.overlijden_edtf;
  const lifeSource = isBirth ? row.life_start_source : row.life_end_source;
  const display = isBirth ? row.geboortedatum_als_bekend : row.overlijdensdatum_als_bekend;
  let badges = "";
  if (edtf && /[~?%]$/.test(String(edtf))) {
    badges += ' <span class="provenance approx" title="Onzekere datum">~</span>';
  }
  if (lifeSource === "shadow" && !(display && String(display).trim())) {
    badges += ' <span class="provenance geschat" title="Geschat uit aanstellingen">geschat</span>';
  }
  return badges;
}

function groupNestedHits(hits, outerKey, innerKey) {
  const groups = [];
  const outerMap = new Map();
  for (const row of hits) {
    const outerId = row[`${outerKey}_id`];
    const innerId = row[`${innerKey}_id`];
    let outer = outerMap.get(outerId);
    if (!outer) {
      outer = { id: outerId, naam: row[outerKey], inner: new Map() };
      outerMap.set(outerId, outer);
      groups.push(outer);
    }
    let inner = outer.inner.get(innerId);
    if (!inner) {
      inner = { id: innerId, naam: row[innerKey], rows: [] };
      outer.inner.set(innerId, inner);
    }
    inner.rows.push(row);
  }
  return groups.map((outer) => ({
    ...outer,
    inner: [...outer.inner.values()],
  }));
}

async function fetchEntityName(entity, id) {
  const res = await fetch(`/api/${entity}/${id}`);
  if (!res.ok) return null;
  const data = await res.json();
  return { id: data.id, naam: data.naam };
}

async function wireSuggest(inputEl, listEl, field, periodSelect, onSelect) {
  let timer;
  inputEl.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      const q = inputEl.value.trim();
      if (q.length < 2) {
        listEl.innerHTML = "";
        listEl.hidden = true;
        return;
      }
      const params = new URLSearchParams({
        q,
        period: periodValue(periodSelect) || "",
        period_mode: periodMode(periodSelect),
      });
      const res = await fetch(`/api/suggest/${field}?${params}`);
      const items = await res.json();
      listEl.innerHTML = "";
      if (!items.length) {
        const li = document.createElement("li");
        li.className = "suggest-empty";
        li.textContent = "Geen suggesties in deze periode";
        listEl.appendChild(li);
        listEl.hidden = false;
        return;
      }
      for (const item of items) {
        const li = document.createElement("li");
        li.textContent = item.naam;
        li.addEventListener("click", () => {
          inputEl.value = "";
          listEl.hidden = true;
          onSelect(item);
        });
        listEl.appendChild(li);
      }
      listEl.hidden = !items.length;
    }, 200);
  });
}

function createChipPicker(inputId, suggestId, chipsId, field, filterKey, periodSelect, maxItems = MAX_CHIP_ITEMS) {
  const inputEl = document.getElementById(inputId);
  const listEl = document.getElementById(suggestId);
  const chipsEl = document.getElementById(chipsId);
  const selected = [];

  function renderChips() {
    chipsEl.innerHTML = "";
    for (const item of selected) {
      const li = document.createElement("li");
      li.className = "chip";
      const label = document.createElement("span");
      label.textContent = item.naam;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.setAttribute("aria-label", "verwijderen");
      btn.textContent = "×";
      btn.addEventListener("click", () => {
        const idx = selected.findIndex((s) => s.id === item.id);
        if (idx >= 0) selected.splice(idx, 1);
        renderChips();
      });
      li.append(label, btn);
      chipsEl.appendChild(li);
    }
  }

  wireSuggest(inputEl, listEl, field, periodSelect, (item) => {
    if (selected.some((s) => s.id === item.id)) return;
    if (selected.length >= maxItems) return;
    selected.push(item);
    renderChips();
  });

  return {
    ids() {
      return selected.map((s) => s.id);
    },
    addToFilters(filters) {
      const ids = this.ids();
      if (ids.length) filters[filterKey] = ids.map(String);
    },
    seed(item) {
      if (!item || selected.some((s) => s.id === item.id)) return;
      if (selected.length >= maxItems) return;
      selected.push(item);
      renderChips();
    },
  };
}

function createGeoPicker(inputId, suggestId, chipsId, field, periodSelect) {
  const mapping = {
    provincie: "provincie_id",
    regio: "regio_id",
    lokaal: "lokaal_id",
  };
  const picker = createChipPicker(inputId, suggestId, chipsId, field, mapping[field], periodSelect);
  return {
    ids: () => picker.ids(),
    addGeoFilters(filters) {
      picker.addToFilters(filters);
    },
    seed: (item) => picker.seed(item),
  };
}

function createStandFilter(containerId, maxItems = MAX_CHIP_ITEMS) {
  const container = document.getElementById(containerId);
  const selected = new Set();
  let loaded = false;

  async function ensureLoaded() {
    if (loaded || !container) return;
    const res = await fetch("/api/stands");
    const stands = await res.json();
    container.innerHTML = "";
    for (const stand of stands) {
      const label = document.createElement("label");
      label.className = "stand-option";
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.value = String(stand.id);
      cb.addEventListener("change", () => {
        const id = stand.id;
        if (cb.checked) {
          if (selected.size >= maxItems) {
            cb.checked = false;
            return;
          }
          selected.add(id);
        } else {
          selected.delete(id);
        }
      });
      label.append(cb, document.createTextNode(` ${stand.naam}`));
      container.appendChild(label);
    }
    loaded = true;
  }

  return {
    prepare: ensureLoaded,
    addToFilters(filters) {
      if (selected.size) {
        filters.stand_id = [...selected].map(String);
      }
    },
  };
}

function addAdelFilter(form, filters) {
  const adel = form.querySelector('input[name="adel"]');
  if (adel?.checked) {
    filters.adel = ["1"];
  }
}

function renderPagination(container, { total, offset, pageSize, onPageChange }) {
  if (!container) return;
  container.innerHTML = "";
  if (!total) return;

  const start = offset + 1;
  const end = Math.min(offset + pageSize, total);
  const info = document.createElement("span");
  info.className = "page-info";
  info.textContent = `${start}–${end} van ${total}`;
  container.appendChild(info);

  const prev = document.createElement("button");
  prev.type = "button";
  prev.className = "page-button";
  prev.textContent = "Vorige";
  prev.disabled = offset <= 0;
  prev.addEventListener("click", () => onPageChange(Math.max(0, offset - pageSize)));
  container.appendChild(prev);

  const next = document.createElement("button");
  next.type = "button";
  next.className = "page-button";
  next.textContent = "Volgende";
  next.disabled = offset + pageSize >= total;
  next.addEventListener("click", () => onPageChange(offset + pageSize));
  container.appendChild(next);
}

function updateSortableHeaders(table, activeSort) {
  if (!table) return;
  for (const th of table.querySelectorAll("th[data-sort]")) {
    th.classList.toggle("sort-active", th.dataset.sort === activeSort);
  }
}

function wireSortableHeaders(table, getSort, setSort, onSort) {
  if (!table) return;
  for (const th of table.querySelectorAll("th[data-sort]")) {
    th.classList.add("sortable");
    th.addEventListener("click", () => {
      setSort(th.dataset.sort);
      updateSortableHeaders(table, getSort());
      onSort();
    });
  }
  updateSortableHeaders(table, getSort());
}

function createAzBrowser(containerId, entity, periodSelect, { onSelect, onClear } = {}) {
  const container = document.getElementById(containerId);
  let activeLetter = null;
  let letterCounts = {};

  function render() {
    if (!container) return;
    container.innerHTML = "";
    const allBtn = document.createElement("button");
    allBtn.type = "button";
    allBtn.className = `az-letter${activeLetter == null ? " active" : ""}`;
    allBtn.textContent = "Alles";
    allBtn.addEventListener("click", () => {
      activeLetter = null;
      render();
      onClear?.();
    });
    container.appendChild(allBtn);

    const letters = [..."ABCDEFGHIJKLMNOPQRSTUVWXYZ", "#"];
    for (const letter of letters) {
      const count = letterCounts[letter] || 0;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `az-letter${activeLetter === letter ? " active" : ""}`;
      btn.textContent = letter;
      btn.disabled = count === 0;
      btn.title = count ? `${count} treffers` : "geen";
      btn.addEventListener("click", () => {
        activeLetter = letter;
        render();
        onSelect?.(letter);
      });
      container.appendChild(btn);
    }
  }

  async function refreshCounts() {
    const params = new URLSearchParams({
      letter: "ALL",
      size: "1",
      from: "0",
      period_mode: periodMode(periodSelect),
    });
    const period = periodValue(periodSelect);
    if (period) params.set("period", period);
    const res = await fetch(`/api/browse/${entity}/az?${params}`);
    const data = await res.json();
    letterCounts = {};
    for (const row of data.letters || []) {
      letterCounts[row.letter] = row.count;
    }
    render();
  }

  function getLetter() {
    return activeLetter;
  }

  function clear() {
    activeLetter = null;
    render();
  }

  render();
  return { refreshCounts, getLetter, clear };
}
