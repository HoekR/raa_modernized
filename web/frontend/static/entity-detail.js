function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderEntityProfile(container, profile) {
  container.innerHTML = "";
  const header = document.createElement("header");
  header.className = "entity-header";
  header.innerHTML = `<h2>${escapeHtml(profile.naam)}</h2>`;
  container.appendChild(header);

  if (profile.stats?.length) {
    const dl = document.createElement("dl");
    dl.className = "entity-stats";
    for (const stat of profile.stats) {
      const dt = document.createElement("dt");
      dt.textContent = stat.label;
      const dd = document.createElement("dd");
      if (stat.html) {
        dd.innerHTML = stat.html;
      } else {
        dd.textContent = String(stat.value);
      }
      dl.append(dt, dd);
    }
    container.appendChild(dl);
  }

  if (profile.actions?.length) {
    const nav = document.createElement("nav");
    nav.className = "entity-actions";
    for (const action of profile.actions) {
      const a = document.createElement("a");
      a.href = action.href;
      a.textContent = action.label;
      nav.appendChild(a);
    }
    container.appendChild(nav);
  }

  for (const section of profile.sections || []) {
    if (!section.html && !section.text) continue;
    const block = document.createElement("section");
    block.className = "entity-section";
    const h3 = document.createElement("h3");
    h3.textContent = section.title;
    block.appendChild(h3);
    const body = document.createElement("div");
    body.className = "entity-section-body";
    if (section.html) {
      body.innerHTML = section.html;
    } else {
      body.textContent = section.text;
    }
    block.appendChild(body);
    container.appendChild(block);
  }

  for (const group of profile.related || []) {
    if (!group.items?.length) continue;
    const block = document.createElement("section");
    block.className = "entity-related";
    const h3 = document.createElement("h3");
    h3.textContent = group.title;
    block.appendChild(h3);
    const ul = document.createElement("ul");
    ul.className = "entity-related-list";
    for (const item of group.items) {
      const li = document.createElement("li");
      const link = document.createElement("a");
      link.href = item.href || "#";
      const count = item.aanstelling_count != null ? ` (${item.aanstelling_count})` : "";
      const meta = item.meta ? ` — ${item.meta}` : "";
      link.textContent = `${item.naam}${count}${meta}`;
      li.appendChild(link);
      ul.appendChild(li);
    }
    block.appendChild(ul);
    container.appendChild(block);
  }
}

function showEntityDetailView({ searchPanel, resultsSection, detailSection, detailBody }) {
  searchPanel.hidden = true;
  resultsSection.hidden = true;
  detailSection.hidden = false;
  if (detailBody) detailBody.innerHTML = "";
}

function hideEntityDetailView({ searchPanel, resultsSection, detailSection }) {
  detailSection.hidden = true;
  searchPanel.hidden = false;
  resultsSection.hidden = false;
}
