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
  return [row.voornaam, row.tussenvoegsel, row.geslachtsnaam].filter(Boolean).join(" ");
}

function personDetailUrl(personId) {
  return `/static/index.html?person=${personId}`;
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

function createChipPicker(inputId, suggestId, chipsId, field, filterKey, periodSelect) {
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
    if (!selected.some((s) => s.id === item.id)) {
      selected.push(item);
      renderChips();
    }
  });

  return {
    ids() {
      return selected.map((s) => s.id);
    },
    addToFilters(filters) {
      const ids = this.ids();
      if (ids.length) filters[filterKey] = ids.map(String);
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
  };
}
