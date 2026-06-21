const data = REPORT_DATA;
const categoryIds = Object.keys(data.categories);
const plan = data.researchPlan;

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

function renderResearchPlan() {
  $("planSummary").innerHTML = plan.summary.map((item) => `<p>${escapeHtml(item)}</p>`).join("");

  const ladder = [
    ["scan", "111", "全部标题、摘要、关键词，建立全局地图"],
    ["broad_read", (plan.levelCounts.broad_read || 0) + (plan.levelCounts.close_read || 0) + (plan.levelCounts.deep_dive || 0), "泛读以上论文，记录输入输出、数据、模型和指标"],
    ["close_read", plan.levelCounts.close_read || 0, "写 1 页精读笔记，核对实验设计和 baseline"],
    ["deep_dive", plan.levelCounts.deep_dive || 0, "代码、数据或实验级深挖，形成方向判断"],
  ];
  $("readingLadder").innerHTML = ladder.map(([id, count, text]) => `
    <article class="ladder-card level-${id}">
      <div class="ladder-count">${escapeHtml(count)}</div>
      <h3>${escapeHtml(plan.readingLevels[id].name)}</h3>
      <p>${escapeHtml(text)}</p>
    </article>
  `).join("");

  $("quotaTable").innerHTML = `
    <div class="quota-row quota-head">
      <span>主题</span><span>深挖</span><span>精读</span><span>泛读</span><span>扫读</span>
    </div>
    ${categoryIds.map((id) => {
      const quota = plan.quotaByCategory[id];
      return `
        <div class="quota-row">
          <span><i style="background:${category(id).color}"></i>${escapeHtml(quota.category)}</span>
          <strong>${quota.deep}</strong>
          <strong>${quota.close}</strong>
          <strong>${quota.broad}</strong>
          <strong>${quota.scan}</strong>
        </div>
      `;
    }).join("")}
  `;

  $("phaseTimeline").innerHTML = plan.phases.map((phase, index) => `
    <article class="phase-item">
      <div class="phase-index">${index + 1}</div>
      <div>
        <h3>${escapeHtml(phase.name)}</h3>
        <span>${escapeHtml(phase.duration)}</span>
        <p>${escapeHtml(phase.goal)}</p>
      </div>
    </article>
  `).join("");

  $("understandingGoals").innerHTML = plan.understandingGoals.map((item) => `<p>${escapeHtml(item)}</p>`).join("");
  $("deliverableList").innerHTML = [
    ...plan.deliverables,
    ...plan.qualityChecks,
  ].map((item) => `<p>${escapeHtml(item)}</p>`).join("");
}

function initControls() {
  $("categoryFilter").innerHTML = `<option value="all">全部主题</option>` + categoryIds.map((id) => `<option value="${id}">${escapeHtml(category(id).short)}</option>`).join("");
  $("levelFilter").innerHTML = `<option value="all">全部等级</option>` + Object.entries(plan.readingLevels)
    .sort(([, a], [, b]) => b.rank - a.rank)
    .map(([id, level]) => `<option value="${id}">${escapeHtml(level.name)}</option>`)
    .join("");
  $("categoryFilter").addEventListener("change", renderPapers);
  $("levelFilter").addEventListener("change", renderPapers);
  $("searchInput").addEventListener("input", renderPapers);
  $("sortMode").addEventListener("change", renderPapers);
}

function paperMatches(paper, selected, level, query) {
  const inCategory = selected === "all" || paper.primary === selected || paper.secondary.includes(selected);
  const inLevel = level === "all" || paper.readingLevel === level;
  if (!inCategory) return false;
  if (!inLevel) return false;
  if (!query) return true;
  const haystack = [
    paper.title,
    paper.abstract,
    paper.authors.join(" "),
    paper.keywords.join(" "),
    paper.session,
    paper.task,
    paper.modality,
    paper.modelFamily,
  ].join(" ").toLowerCase();
  return haystack.includes(query);
}

function sortPapers(papers, mode) {
  const sorted = [...papers];
  if (mode === "session") sorted.sort((a, b) => Number(a.session) - Number(b.session) || a.title.localeCompare(b.title));
  if (mode === "confidence") sorted.sort((a, b) => b.confidence - a.confidence || a.title.localeCompare(b.title));
  if (mode === "title") sorted.sort((a, b) => a.title.localeCompare(b.title));
  if (mode === "category") sorted.sort((a, b) => a.primary.localeCompare(b.primary) || a.title.localeCompare(b.title));
  if (mode === "priority") {
    sorted.sort((a, b) => {
      const rankDiff = plan.readingLevels[b.readingLevel].rank - plan.readingLevels[a.readingLevel].rank;
      return rankDiff || b.priorityScore - a.priorityScore || a.title.localeCompare(b.title);
    });
  }
  return sorted;
}

function renderPapers() {
  const selected = $("categoryFilter").value;
  const level = $("levelFilter").value;
  const query = $("searchInput").value.trim().toLowerCase();
  const mode = $("sortMode").value;
  const filtered = sortPapers(data.papers.filter((paper) => paperMatches(paper, selected, level, query)), mode);
  $("resultMeta").textContent = `显示 ${filtered.length} / ${data.papers.length} 篇`;
  $("paperGrid").innerHTML = filtered.map((paper) => {
    const meta = category(paper.primary);
    const levelMeta = plan.readingLevels[paper.readingLevel];
    const secondary = paper.secondary.map((id) => `<span class="tag" style="background:${category(id).color}">${escapeHtml(category(id).short)}</span>`).join("");
    const summary = paper.tldr || paper.abstract || "暂无摘要。";
    return `
      <article class="paper-card">
        <div class="paper-badges">
          <span class="tag" style="background:${meta.color}">${escapeHtml(meta.short)}</span>
          <span class="read-tag level-${paper.readingLevel}">${escapeHtml(levelMeta.short)}</span>
        </div>
        <h3>${escapeHtml(paper.title)}</h3>
        <p>${escapeHtml(paper.authors.slice(0, 4).join(", "))}${paper.authors.length > 4 ? " 等" : ""}</p>
        <div class="paper-meta">
          <span class="meta-chip">S${escapeHtml(paper.session)}</span>
          <span class="meta-chip">${escapeHtml(paper.task)}</span>
          <span class="meta-chip">${escapeHtml(paper.modality)}</span>
          ${secondary}
        </div>
        <p>${escapeHtml(summary.slice(0, 260))}${summary.length > 260 ? "..." : ""}</p>
        <p class="matrix-note">矩阵记录：${escapeHtml(paper.modelFamily)} · ${escapeHtml(paper.evaluationFocus)}</p>
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
renderResearchPlan();
initControls();
renderPapers();
