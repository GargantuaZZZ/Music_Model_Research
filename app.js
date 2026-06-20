const data = REPORT_DATA;
const categoryIds = Object.keys(data.categories);

const $ = (id) => document.getElementById(id);
const category = (id) => data.categories[id] || data.categories.understanding;

function escapeHtml(text) {
  return String(text || "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[char]);
}

function initMetrics() {
  $("paperCount").textContent = data.source.paperCount;
  $("categoryCount").textContent = categoryIds.length;
  $("sessionCount").textContent = Object.keys(data.sessionCounts).length;
  $("crossCount").textContent = data.papers.filter((paper) => paper.secondary.length).length;
}

function renderCategoryChart() {
  const max = Math.max(...Object.values(data.categoryCounts));
  $("categoryChart").innerHTML = categoryIds.map((id) => {
    const meta = category(id);
    const count = data.categoryCounts[id] || 0;
    const pct = max ? Math.round((count / max) * 100) : 0;
    return `
      <div class="bar-row">
        <strong>${escapeHtml(meta.short)}</strong>
        <div class="bar-track"><div class="bar-fill" style="width:${pct}%; background:${meta.color}"></div></div>
        <span>${count}</span>
      </div>
    `;
  }).join("");
}

function renderNarrative() {
  $("categoryNarrative").innerHTML = categoryIds.map((id) => {
    const meta = category(id);
    return `
      <article class="narrative-card">
        <span class="tag" style="background:${meta.color}">${escapeHtml(meta.short)}</span>
        <h3>${escapeHtml(meta.name)}</h3>
        <p>${escapeHtml(data.categoryInsights[id] || meta.description)}</p>
      </article>
    `;
  }).join("");
}

function renderTrends() {
  $("trendGrid").innerHTML = data.trends.map((trend) => `
    <article class="trend-card">
      <div class="trend-count">${trend.count}</div>
      <h3>${escapeHtml(trend.title)}</h3>
      <ul class="mini-list">
        ${trend.examples.slice(0, 3).map((paper) => `<li>${escapeHtml(paper.title)}</li>`).join("")}
      </ul>
    </article>
  `).join("");
}

function renderHeatmap() {
  const max = Math.max(...Object.values(data.sessionCounts).flatMap((row) => categoryIds.map((id) => row[id] || 0)));
  const header = `<div class="heat-row"><strong></strong>${categoryIds.map((id) => `<strong title="${escapeHtml(category(id).name)}">${escapeHtml(category(id).short.slice(0, 2))}</strong>`).join("")}</div>`;
  const rows = Object.entries(data.sessionCounts).map(([session, row]) => `
    <div class="heat-row">
      <strong>S${escapeHtml(session)}</strong>
      ${categoryIds.map((id) => {
        const count = row[id] || 0;
        const alpha = max ? 0.08 + (count / max) * 0.72 : 0.08;
        return `<div class="heat-cell" title="${escapeHtml(category(id).name)}: ${count}" style="background: color-mix(in srgb, ${category(id).color} ${Math.round(alpha * 100)}%, white)">${count || ""}</div>`;
      }).join("")}
    </div>
  `).join("");
  $("heatmap").innerHTML = header + rows;
}

function renderKeywords() {
  const max = Math.max(...data.topKeywords.map(([, count]) => count));
  $("keywordCloud").innerHTML = data.topKeywords.map(([keyword, count]) => {
    const size = 12 + Math.round((count / max) * 8);
    return `<span class="keyword" style="font-size:${size}px">${escapeHtml(keyword)} · ${count}</span>`;
  }).join("");
}

function renderRoutes() {
  $("routeList").innerHTML = data.routes.map((route) => `
    <article class="route-card">
      <h3>${escapeHtml(route.title)}</h3>
      <p>${escapeHtml(route.text)}</p>
    </article>
  `).join("");
}

function initControls() {
  $("categoryFilter").innerHTML = `<option value="all">全部主题</option>` + categoryIds.map((id) => `<option value="${id}">${escapeHtml(category(id).short)}</option>`).join("");
  $("categoryFilter").addEventListener("change", renderPapers);
  $("searchInput").addEventListener("input", renderPapers);
  $("sortMode").addEventListener("change", renderPapers);
}

function paperMatches(paper, selected, query) {
  const inCategory = selected === "all" || paper.primary === selected || paper.secondary.includes(selected);
  if (!inCategory) return false;
  if (!query) return true;
  const haystack = [
    paper.title,
    paper.abstract,
    paper.authors.join(" "),
    paper.keywords.join(" "),
    paper.session,
  ].join(" ").toLowerCase();
  return haystack.includes(query);
}

function sortPapers(papers, mode) {
  const sorted = [...papers];
  if (mode === "session") sorted.sort((a, b) => Number(a.session) - Number(b.session) || a.title.localeCompare(b.title));
  if (mode === "confidence") sorted.sort((a, b) => b.confidence - a.confidence || a.title.localeCompare(b.title));
  if (mode === "title") sorted.sort((a, b) => a.title.localeCompare(b.title));
  if (mode === "category") sorted.sort((a, b) => a.primary.localeCompare(b.primary) || a.title.localeCompare(b.title));
  return sorted;
}

function renderPapers() {
  const selected = $("categoryFilter").value;
  const query = $("searchInput").value.trim().toLowerCase();
  const mode = $("sortMode").value;
  const filtered = sortPapers(data.papers.filter((paper) => paperMatches(paper, selected, query)), mode);
  $("resultMeta").textContent = `显示 ${filtered.length} / ${data.papers.length} 篇`;
  $("paperGrid").innerHTML = filtered.map((paper) => {
    const meta = category(paper.primary);
    const secondary = paper.secondary.map((id) => `<span class="tag" style="background:${category(id).color}">${escapeHtml(category(id).short)}</span>`).join("");
    const summary = paper.tldr || paper.abstract || "暂无摘要。";
    return `
      <article class="paper-card">
        <span class="tag" style="background:${meta.color}">${escapeHtml(meta.short)}</span>
        <h3>${escapeHtml(paper.title)}</h3>
        <p>${escapeHtml(paper.authors.slice(0, 4).join(", "))}${paper.authors.length > 4 ? " 等" : ""}</p>
        <div class="paper-meta">
          <span class="keyword">S${escapeHtml(paper.session)}</span>
          <span class="keyword">置信度 ${Math.round(paper.confidence * 100)}%</span>
          ${secondary}
        </div>
        <p>${escapeHtml(summary.slice(0, 260))}${summary.length > 260 ? "..." : ""}</p>
        <div class="paper-actions">
          <a href="${paper.sourceUrl}" target="_blank" rel="noreferrer">ISMIR 页面</a>
          ${paper.pdf ? `<a href="${paper.pdf}" target="_blank" rel="noreferrer">PDF</a>` : ""}
          ${paper.video ? `<a href="${paper.video}" target="_blank" rel="noreferrer">Video</a>` : ""}
        </div>
      </article>
    `;
  }).join("");
}

initMetrics();
renderCategoryChart();
renderNarrative();
renderTrends();
renderHeatmap();
renderKeywords();
renderRoutes();
initControls();
renderPapers();
