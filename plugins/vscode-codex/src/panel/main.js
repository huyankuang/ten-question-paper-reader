// Ten-Question Paper Reader — Webview frontend (vanilla JS)
const vscode = acquireVsCodeApi();

const statusEl = document.getElementById('status');
const contentEl = document.getElementById('content');
document.getElementById('select-pdf').addEventListener('click', () => {
  vscode.postMessage({ type: 'select-pdf' });
});

let currentResult = null;
let glossary = {};

window.addEventListener('message', event => {
  const msg = event.data;
  if (msg.type === 'status') {
    statusEl.textContent = msg.text;
    statusEl.className = 'status active';
  } else if (msg.type === 'error') {
    statusEl.textContent = msg.text;
    statusEl.className = 'status error';
  } else if (msg.type === 'result') {
    currentResult = msg.data;
    glossary = msg.data.glossary || {};
    renderResult(msg.data);
    statusEl.className = 'status';
  } else if (msg.type === 'evaluation') {
    renderEvaluation(msg.data);
  }
});

function renderResult(data) {
  let html = `<h2>${escapeHtml(data.paper_title || '论文精读')}</h2>`;
  html += `<div class="tabs"><button class="tab active" data-tab="short">精简概览</button><button class="tab" data-tab="full">深度精读</button><button class="tab" data-tab="summary">我的总结</button></div>`;

  // Short view
  html += `<div class="tab-pane" id="pane-short">`;
  data.qa_pairs.forEach(qa => {
    html += `<div class="qa"><span class="qid">Q${qa.id}</span><strong>${escapeHtml(qa.question)}</strong>
      <span class="badge">${escapeHtml(qa.type)}</span>
      <span class="confidence">置信度:${escapeHtml(qa.confidence)}</span>
      <p>${highlightTerms(escapeHtml(qa.short_answer))}</p></div>`;
  });
  html += `</div>`;

  // Full view
  html += `<div class="tab-pane hidden" id="pane-full">`;
  data.qa_pairs.forEach(qa => {
    html += `<div class="qa"><span class="qid">Q${qa.id}</span><strong>${escapeHtml(qa.question)}</strong>
      <div class="citation">📖 ${escapeHtml(qa.citation || '原文未明确')}</div>
      <div class="full-answer">${highlightTerms(escapeHtml(qa.full_answer))}</div></div>`;
  });
  html += `</div>`;

  // Summary view
  html += `<div class="tab-pane hidden" id="pane-summary">
    <p class="hint">对照原文精读后，把你的理解写在下面（可用十问框架填空）：</p>
    <textarea id="user-summary" rows="12" placeholder="Q1: ...&#10;Q2: ...&#10;..."></textarea>
    <div class="btn-row">
      <button id="btn-evaluate">AI评价我的总结</button>
      <button id="btn-export">导出精读笔记</button>
    </div>
    <div id="eval-result"></div>
  </div>`;

  contentEl.innerHTML = html;

  // Tab switching
  document.querySelectorAll('.tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.add('hidden'));
      document.getElementById('pane-' + btn.dataset.tab).classList.remove('hidden');
    });
  });

  // Term click popover
  document.querySelectorAll('.term').forEach(el => {
    el.addEventListener('click', () => {
      const term = el.dataset.term;
      const def = glossary[term] || '（暂无预生成解释，可复制到对话框提问）';
      showPopover(el, term, def);
    });
  });

  // Evaluate
  document.getElementById('btn-evaluate').addEventListener('click', () => {
    const summary = document.getElementById('user-summary').value;
    if (!summary.trim()) { alert('请先写总结'); return; }
    vscode.postMessage({ type: 'evaluate', payload: { noteJsonPath: '', summary } });
  });

  // Export
  document.getElementById('btn-export').addEventListener('click', () => {
    const md = buildMarkdown(data, document.getElementById('user-summary').value);
    vscode.postMessage({ type: 'export-md', payload: { markdown: md } });
  });
}

function highlightTerms(text) {
  let out = text;
  Object.keys(glossary).sort((a, b) => b.length - a.length).forEach(term => {
    const re = new RegExp(escapeRegExp(term), 'g');
    out = out.replace(re, `<span class="term" data-term="${escapeHtml(term)}">${escapeHtml(term)}</span>`);
  });
  return out;
}

function showPopover(el, term, def) {
  let pop = document.querySelector('.popover');
  if (pop) pop.remove();
  pop = document.createElement('div');
  pop.className = 'popover';
  pop.innerHTML = `<strong>${escapeHtml(term)}</strong><p>${escapeHtml(def)}</p>`;
  document.body.appendChild(pop);
  const rect = el.getBoundingClientRect();
  pop.style.top = (rect.bottom + window.scrollY + 5) + 'px';
  pop.style.left = rect.left + 'px';
  setTimeout(() => document.addEventListener('click', () => pop.remove(), { once: true }));
}

function renderEvaluation(ev) {
  const el = document.getElementById('eval-result');
  if (!el) return;
  let html = `<div class="eval-card"><h3>AI评价：${ev.score}分</h3>`;
  if (ev.dimension_scores) {
    html += '<ul>';
    for (const [k, v] of Object.entries(ev.dimension_scores)) {
      html += `<li>${k}: ${v}/25</li>`;
    }
    html += '</ul>';
  }
  if (ev.strengths?.length) {
    html += '<p><b>优点：</b></p><ul>' + ev.strengths.map(s => `<li>${escapeHtml(s)}</li>`).join('') + '</ul>';
  }
  if (ev.suggestions?.length) {
    html += '<p><b>建议：</b></p><ul>' + ev.suggestions.map(s => `<li>${escapeHtml(s)}</li>`).join('') + '</ul>';
  }
  html += '</div>';
  el.innerHTML = html;
}

function buildMarkdown(data, userSummary) {
  let md = `# 精读笔记：${data.paper_title}\n\n## 十问拆解\n\n`;
  data.qa_pairs.forEach(qa => {
    md += `### Q${qa.id}. ${qa.question}\n- 类型：${qa.type}\n- 置信度：${qa.confidence}\n- 原文定位：${qa.citation}\n\n${qa.full_answer}\n\n`;
  });
  if (userSummary) md += `## 我的总结\n\n${userSummary}\n\n`;
  if (Object.keys(data.glossary || {}).length) {
    md += `## 核心术语表\n\n`;
    for (const [t, d] of Object.entries(data.glossary)) md += `- **${t}**：${d}\n`;
  }
  return md;
}

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}
function escapeRegExp(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
