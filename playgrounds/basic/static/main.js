/* globals fetch, navigator, alert, document, window */

const $ = sel => document.querySelector(sel);
const $$ = sel => [...document.querySelectorAll(sel)];

let SETTINGS = null;
let DEBUG = [];

/* ----------------------------- Prompt Templates ----------------------------- */
// Prompt templates (use {owner_repo}, {start_date}, {end_date}, {capacity_points}, {selected_labels}, {exclude_labels}, {milestone_name})
const PROMPT_TEMPLATES = [
  {
    id: "short",
    name: "Short & sweet",
    text: "Get the open GitHub issues for my next sprint backlog."
  },
  {
    id: "repo_minimal",
    name: "Repo + minimal filters (recommended)",
    text:
`From {owner_repo}, collect OPEN issues (exclude PRs) updated in the last 30 days for the next sprint backlog.
Prioritize by priority label (P0, P1, P2), then by updated_at.
Include title, #number, labels, updated_at, url and a 1-sentence summary per issue.`
  },
  {
    id: "sprint_window_capacity",
    name: "Sprint window + capacity",
    text:
`From {owner_repo}, propose a next sprint backlog for {start_date}–{end_date} with roughly {capacity_points} story points.
Use OPEN issues only; prefer labels feature, bug, chore. Include estimate (if present), priority, and dependencies/blockers inferred from comments.`
  },
  {
    id: "labels_exclusions",
    name: "Labels & exclusions",
    text:
`Build the next sprint backlog from {owner_repo} using OPEN issues with labels in {selected_labels} and excluding {exclude_labels}.
De-dupe near-duplicates, split multi-work items into sub-tasks, and order by P0→P1→P2, then updated_at.`
  },
  {
    id: "milestone",
    name: "Milestone aware",
    text:
`For {owner_repo}, assemble OPEN issues suitable for the “{milestone_name}” milestone as the next sprint backlog.
Show #number, title, labels, estimate/points, assignee, last activity, url, and a one-line “why now”.`
  },
  {
    id: "comments_informed",
    name: "Comments-informed prioritization",
    text:
`From {owner_repo}, create a next sprint backlog of OPEN issues.
Use the latest issue comments to surface blockers, design links, acceptance criteria and summarize them in ≤2 lines per item.
Prioritize P0 and items with clear acceptance criteria.`
  },
  {
    id: "json_schema",
    name: "Output format (JSON schema)",
    text:
`From {owner_repo}, return a next sprint backlog of OPEN issues. For each item:
{ "number": n, "title": "...", "priority": "P0|P1|P2|none", "labels": [], "estimate": "n|unknown", "updated_at": "ISO", "url": "...", "summary": "≤25 words", "blockers": "≤15 words" }.
Order by priority then updated_at.`
  },
  {
    id: "concrete_repo",
    name: "Concrete example (from Settings repo)",
    text:
`From {owner_repo}, build the next sprint backlog of OPEN issues (exclude PRs).
Include #number, title, labels, updated_at, url and a one-line summary per issue; if comments exist, add blockers/next step in ≤15 words. Sort by P0→P1→P2, then updated_at desc.`
  },
  {
    id: "capacity_quickwins",
    name: "Capacity + quick wins",
    text:
`From {owner_repo}, pick OPEN issues for next sprint with mix: 60% quick wins (<1 day), 40% medium (1–3 days).
Show #number, title, est, labels, url, and 1-line “why it fits now”. Prioritize customer impact and unblockers.`
  },
  {
    id: "grooming",
    name: "Backlog grooming tone",
    text:
`Groom the next sprint backlog from {owner_repo} (OPEN issues only). Flag duplicates, suggest label fixes, and propose top 10 in execution order with a crisp next action each.`
  },
  {
    id: "research_papers",
    name: "Research Paper Analysis",
    text:
`Analyze GitHub issues from {owner_repo} and match them with relevant AI research papers. Provide:
1. Key requirements extracted from GitHub issues
2. Relevant research papers that address these requirements
3. Implementation recommendations based on research findings
4. Gap analysis and potential research opportunities`
  },
  {
    id: "literature_review",
    name: "Literature Review",
    text:
`Conduct a literature review using GitHub issues from {owner_repo} and research papers. Focus on:
1. Current state of the field based on GitHub discussions
2. Relevant research papers and their contributions
3. Research gaps identified from GitHub issues
4. Future research directions and collaboration opportunities`
  },
  {
    id: "implementation_guide",
    name: "Implementation Guide",
    text:
`Create an implementation guide by combining GitHub issues from {owner_repo} with research paper insights. Include:
1. Technical requirements from GitHub issues
2. Recommended approaches from research papers
3. Architecture and design patterns
4. Potential challenges and mitigation strategies`
  },
];

const MODEL_OPTIONS = {
  openai: ["gpt-5", "gpt-4o", "o4-mini"],
  anthropic: ["claude-opus-4-0", "claude-sonnet-4-0", "claude-3-7-sonnet-latest", "claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"],
  ollama: ["gemma3:270m", "gpt-oss:20b", "llama3.2:3b"],
  google: ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"],
};

/* ----------------------------- Date/Helpers ----------------------------- */

function nextMonday(d = new Date()) {
  const dt = new Date(d);
  const day = dt.getDay(); // 0=Sun,..6=Sat
  const diff = (8 - (day || 7)) % 7; // days until next Monday
  dt.setDate(dt.getDate() + (diff === 0 ? 7 : diff)); // if today is Monday, pick *next* Monday
  dt.setHours(0,0,0,0);
  return dt;
}

function addDays(date, days) {
  const dt = new Date(date);
  dt.setDate(dt.getDate() + days);
  return dt;
}

function isoDate(date) {
  // Asia/Kolkata shown as local; we only need date part
  const y = date.getFullYear();
  const m = String(date.getMonth()+1).padStart(2,'0');
  const d = String(date.getDate()).padStart(2,'0');
  return `${y}-${m}-${d}`;
}

function csvToArray(s) {
  return (s || "")
    .split(",")
    .map(x => x.trim())
    .filter(Boolean);
}

function htmlEscape(s) {
  return String(s || "").replace(/[&<>"']/g, c =>
    ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

/* ----------------------------- Prompt templating ----------------------------- */

function fillPromptTemplate(templateId, settings) {
  const tpl = PROMPT_TEMPLATES.find(t => t.id === templateId) || PROMPT_TEMPLATES[0];
  const repo = (settings?.mcp?.github?.repo || "").trim();
  if (!repo || !repo.includes('/')) {
    return "Get the open GitHub issues for my next sprint backlog.  <!-- Tip: set owner/repo in Settings → MCP GitHub -->";
  }

  const sprintLen = parseInt($('#tpl_sprint_len')?.value || '14', 10);
  const capacity = parseInt($('#tpl_capacity')?.value || '20', 10);

  const includeLabels = csvToArray($('#tpl_labels_include')?.value).map(x => x.replaceAll('"',''));
  const excludeLabels = csvToArray($('#tpl_labels_exclude')?.value).map(x => x.replaceAll('"',''));
  const milestone = ($('#tpl_milestone')?.value || "Next Sprint").trim();

  const start = nextMonday();
  const end = addDays(start, sprintLen - 1);

  const ctx = {
    "{owner_repo}": repo,
    "{start_date}": isoDate(start),
    "{end_date}": isoDate(end),
    "{capacity_points}": String(capacity),
    "{selected_labels}": JSON.stringify(includeLabels.length ? includeLabels : ["feature","bug","chore"]),
    "{exclude_labels}": JSON.stringify(excludeLabels.length ? excludeLabels : ["wontfix","duplicate"]),
    "{milestone_name}": milestone || "Next Sprint",
  };

  let out = tpl.text;
  Object.entries(ctx).forEach(([k, v]) => { out = out.split(k).join(v); });
  return out;
}

function renderPromptPreview() {
  const id = $('#promptTemplate').value;
  const text = fillPromptTemplate(id, SETTINGS);
  $('#previewPrompt').value = text;
}

function populatePromptTemplates() {
  const sel = $('#promptTemplate');
  if (!sel) return;
  sel.innerHTML = '';
  PROMPT_TEMPLATES.forEach(t => {
    const opt = document.createElement('option');
    opt.value = t.id;
    opt.textContent = t.name;
    sel.appendChild(opt);
  });
  sel.value = 'repo_minimal';
  renderPromptPreview();
}

function bindPromptTemplateUI() {
  const sel = $('#promptTemplate');
  const inputs = ['#tpl_sprint_len','#tpl_capacity','#tpl_labels_include','#tpl_labels_exclude','#tpl_milestone'];

  if (sel) sel.addEventListener('change', renderPromptPreview);
  inputs.forEach(id => { const el = $(id); if (el) el.addEventListener('input', renderPromptPreview); });

  const copyBtn = $('#btnCopyPrompt');
  if (copyBtn) copyBtn.addEventListener('click', async () => {
    const text = $('#previewPrompt').value || fillPromptTemplate($('#promptTemplate').value, SETTINGS);
    $('#userPrompt').value = text; // drop into chat input
    try {
      await navigator.clipboard.writeText(text);
      $('#copyStatus').textContent = 'Copied to clipboard & Chat → User Prompt';
      setTimeout(() => $('#copyStatus').textContent = '', 2000);
    } catch {
      $('#copyStatus').textContent = 'Copied to Chat → User Prompt (clipboard blocked)';
      setTimeout(() => $('#copyStatus').textContent = '', 2000);
    }
    activateTab('chat');
  });
}

/* ----------------------------- Debug helpers & UI ----------------------------- */

function logDebug(section, obj) {
  DEBUG.push({ ts: new Date().toISOString(), section, obj });
  // Keep legacy JSON log (fallback panel)
  const legacy = $('#debugLog');
  if (legacy) legacy.textContent = JSON.stringify(DEBUG, null, 2);
}

function getDebugEl() {
  return $('#debug-output') || $('#debugLog'); // prefer structured panel; fallback to legacy <pre id="debugLog">
}

function renderCallTable(calls = []) {
  if (!Array.isArray(calls) || !calls.length) return '<em>No calls</em>';
  let rows = calls.map(c => `
    <tr>
      <td>${htmlEscape(c.tool)}</td>
      <td><pre class="small-pre">${htmlEscape(JSON.stringify(c.input, null, 2))}</pre></td>
      <td>${c.ok ? '✅' : '❌'}</td>
      <td>${c.duration_ms ?? ''}</td>
      <td><pre class="small-pre">${htmlEscape(c.output_preview || c.error || '')}</pre></td>
    </tr>
  `).join('');
  return `
    <table class="debug-table">
      <thead><tr><th>Tool</th><th>Input</th><th>OK</th><th>ms</th><th>Output / Error (preview)</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderDebug(debug) {
  const el = getDebugEl();
  if (!el) return;
  if (!debug) { el.innerHTML = '<em>No debug</em>'; return; }

  const prov = debug.provider || {};
  const gh = (debug.mcp && debug.mcp.github) || {};
  const pg = (debug.mcp && debug.mcp.postgres) || {};

  el.innerHTML = `
    <section>
      <h3>Provider</h3>
      <div><strong>Name:</strong> ${htmlEscape(prov.name || '')}</div>
      <div><strong>Model:</strong> ${htmlEscape(prov.model || '')}</div>
      <div><strong>Endpoint:</strong> ${htmlEscape(prov.endpoint || '')}</div>
      ${prov.error ? `<div class="err"><strong>Error:</strong> ${htmlEscape(prov.error)}</div>` : ''}
      <h4>Request</h4>
      <pre class="small-pre">System (preview):\n${htmlEscape((prov.request && prov.request.system_preview) || '')}</pre>
      <pre class="small-pre">Prompt (preview):\n${htmlEscape((prov.request && prov.request.prompt_preview) || '')}</pre>
      <div><strong>Temperature:</strong> ${htmlEscape(String((prov.request && prov.request.temperature) ?? ''))}</div>
      <h4>Response</h4>
      <pre class="small-pre">${htmlEscape((prov.response && prov.response.raw_preview) || '')}</pre>
      <h4>Parsed</h4>
      <pre class="small-pre">${htmlEscape((prov.parsed && prov.parsed.structured_preview) || '')}</pre>
    </section>

    <hr/>

    <section>
      <h3>MCP — GitHub</h3>
      ${gh && gh.error ? `<div class="err"><strong>Error:</strong> ${htmlEscape(gh.error)}</div>` : ''}
      <div><strong>Tools:</strong> <code>${htmlEscape(JSON.stringify(gh.tools || []))}</code></div>
      ${renderCallTable(gh.calls)}
    </section>

    <hr/>

    <section>
      <h3>MCP — Postgres</h3>
      ${pg && pg.error ? `<div class="err"><strong>Error:</strong> ${htmlEscape(pg.error)}</div>` : ''}
      <div><strong>Tools:</strong> <code>${htmlEscape(JSON.stringify(pg.tools || []))}</code></div>
      <div><strong>SQL:</strong> <code>${htmlEscape(pg.sql || '')}</code></div>
      ${renderCallTable(pg.calls)}
    </section>

    <hr/>

    <section>
      <h3>Optimizer</h3>
      <pre class="small-pre">${htmlEscape(JSON.stringify(debug.optimizer || {}, null, 2))}</pre>
      <div><strong>Final prompt tokens (est):</strong> ${htmlEscape(String(debug.final_prompt_tokens_est || ''))}</div>
    </section>
  `;
}

/* ----------------------------- Tabs ----------------------------- */

function activateTab(name) {
  $$('.tab').forEach(b => b.classList.remove('tab-active'));
  const tabBtn = $(`.tab[data-tab="${name}"]`);
  if (tabBtn) tabBtn.classList.add('tab-active');
  ['chat','debug','settings','templates'].forEach(id => {
    const el = $('#tab-' + id);
    if (el) el.classList.toggle('hidden', id !== name);
  });
}

/* ----------------------------- Settings load/save ----------------------------- */

async function loadSettings() {
  const res = await fetch('/api/settings');
  SETTINGS = await res.json();
  fillSettingsFormFromSettings();
  fillProviderDropdownFromSettings();
  renderMcpSelected();
  populatePromptTemplates();
}

function populateModelSelect(selectEl, providerKey, defaultVal) {
  selectEl.innerHTML = '';
  const options = MODEL_OPTIONS[providerKey] || [];
  options.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m; opt.textContent = m;
    selectEl.appendChild(opt);
  });
  if (defaultVal && !options.includes(defaultVal)) {
    const opt = document.createElement('option');
    opt.value = defaultVal; opt.textContent = defaultVal;
    selectEl.appendChild(opt);
  }
  selectEl.value = defaultVal || options[0] || '';
}

function fillProviderDropdownFromSettings() {
  const provSel = $('#provider');
  const modelSel = $('#model');
  provSel.innerHTML = '';
  const providers = SETTINGS.providers || {};

  Object.entries(providers).forEach(([key, p]) => {
    if (p.enabled) {
      const opt = document.createElement('option');
      opt.value = key;
      opt.textContent = `${p.name} (${key})`;
      provSel.appendChild(opt);
    }
  });

  let chosen = 'anthropic';
  if (!(providers.anthropic && providers.anthropic.enabled)) {
    const first = provSel.options[0];
    chosen = first ? first.value : chosen;
  }
  provSel.value = chosen;
  const defaultModel = providers[chosen]?.default_model || '';
  populateModelSelect(modelSel, chosen, defaultModel);

  provSel.addEventListener('change', () => {
    const k = provSel.value;
    const defModel = providers[k]?.default_model || '';
    populateModelSelect(modelSel, k, defModel);
  });
}

function setOptimizerProviderRadio(value) {
  const map = { openai:'#opt_openai', anthropic:'#opt_anthropic', ollama:'#opt_ollama', google:'#opt_google' };
  Object.values(map).forEach(sel => { const el = $(sel); if (el) el.checked = false; });
  const sel = map[value] || '#opt_anthropic';
  if ($(sel)) $(sel).checked = true;
}

function getOptimizerProviderRadio() {
  const checked = $$('input[name="opt_provider"]:checked')[0];
  return checked ? checked.value : 'anthropic';
}

function wireOptimizerRadio() {
  $$('input[name="opt_provider"]').forEach(el => {
    el.addEventListener('change', () => {
      const k = getOptimizerProviderRadio();
      const defModel = SETTINGS.optimizer?.model || (SETTINGS.providers[k]?.default_model) || (MODEL_OPTIONS[k]?.[0] || '');
      populateModelSelect($('#opt_model'), k, defModel);
    });
  });
}

function fillSettingsFormFromSettings() {
  const p = SETTINGS.providers;

  // OpenAI
  $('#openai_enabled').checked = p.openai.enabled;
  $('#openai_url').value = p.openai.base_url;
  $('#openai_key').value = p.openai.api_key;
  populateModelSelect($('#openai_model'), 'openai', p.openai.default_model);
  $('#openai_temp').value = p.openai.temperature;
  $('#openai_cw').value = p.openai.context_window;

  // Anthropic
  $('#anthropic_enabled').checked = p.anthropic.enabled;
  $('#anthropic_url').value = p.anthropic.base_url;
  $('#anthropic_key').value = p.anthropic.api_key;
  populateModelSelect($('#anthropic_model'), 'anthropic', p.anthropic.default_model);
  $('#anthropic_temp').value = p.anthropic.temperature;
  $('#anthropic_cw').value = p.anthropic.context_window;

  // Ollama
  $('#ollama_enabled').checked = p.ollama.enabled;
  $('#ollama_url').value = p.ollama.base_url;
  populateModelSelect($('#ollama_model'), 'ollama', p.ollama.default_model);
  $('#ollama_temp').value = p.ollama.temperature;
  $('#ollama_cw').value = p.ollama.context_window;

  // Google
  $('#google_enabled').checked = p.google.enabled;
  $('#google_url').value = p.google.base_url;
  $('#google_key').value = p.google.api_key;
  populateModelSelect($('#google_model'), 'google', p.google.default_model);
  $('#google_temp').value = p.google.temperature;
  $('#google_cw').value = p.google.context_window;

  // Optimizer
  const opt = SETTINGS.optimizer || { provider: 'anthropic', model: 'claude-4-sonnet', temperature: 0.2 };
  setOptimizerProviderRadio(opt.provider || 'anthropic');
  populateModelSelect($('#opt_model'), opt.provider || 'anthropic', opt.model || '');
  $('#opt_temp').value = opt.temperature ?? 0.2;

  wireOptimizerRadio();

  // MCP
  const g = SETTINGS.mcp.github;
  $('#gh_enabled').checked = g.enabled;
  $('#gh_url').value = g.url;
  $('#gh_token').value = g.auth_token;
  $('#gh_repo').value = g.repo;

  const pg = SETTINGS.mcp.postgres;
  $('#pg_enabled').checked = pg.enabled;
  $('#pg_url').value = pg.url;
  $('#pg_token').value = pg.auth_token;
  $('#pg_sql').value = pg.sample_sql;
}

async function saveSettingsFromForm(evt) {
  evt.preventDefault();
  const optProvider = getOptimizerProviderRadio();
  const payload = {
    providers: {
      openai: {
        enabled: $('#openai_enabled').checked, name: 'OpenAI',
        base_url: $('#openai_url').value, api_key: $('#openai_key').value,
        default_model: $('#openai_model').value, temperature: parseFloat($('#openai_temp').value || '0.2'),
        context_window: parseInt($('#openai_cw').value || '128000', 10),
      },
      anthropic: {
        enabled: $('#anthropic_enabled').checked, name: 'Anthropic',
        base_url: $('#anthropic_url').value, api_key: $('#anthropic_key').value,
        default_model: $('#anthropic_model').value, temperature: parseFloat($('#anthropic_temp').value || '0.2'),
        context_window: parseInt($('#anthropic_cw').value || '200000', 10),
      },
      ollama: {
        enabled: $('#ollama_enabled').checked, name: 'Ollama',
        base_url: $('#ollama_url').value, api_key: '',
        default_model: $('#ollama_model').value, temperature: parseFloat($('#ollama_temp').value || '0.2'),
        context_window: parseInt($('#ollama_cw').value || '8000', 10),
      },
      google: {
        enabled: $('#google_enabled').checked, name: 'Google',
        base_url: $('#google_url').value, api_key: $('#google_key').value,
        default_model: $('#google_model').value, temperature: parseFloat($('#google_temp').value || '0.2'),
        context_window: parseInt($('#google_cw').value || '128000', 10),
      },
    },
    optimizer: {
      provider: optProvider,
      model: $('#opt_model').value,
      temperature: parseFloat($('#opt_temp').value || '0.2'),
    },
    mcp: {
      github: {
        enabled: $('#gh_enabled').checked,
        url: $('#gh_url').value,
        auth_token: $('#gh_token').value,
        repo: $('#gh_repo').value,
      },
      postgres: {
        enabled: $('#pg_enabled').checked,
        url: $('#pg_url').value,
        auth_token: $('#pg_token').value,
        sample_sql: $('#pg_sql').value,
      }
    }
  };

  const res = await fetch('/api/settings', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
  const ok = await res.json();
  logDebug('settings.save', ok);
  await loadSettings();
  alert('Settings saved');
}

/* ----------------------------- MCP selection chips ----------------------------- */

function renderMcpSelected() {
  const wrap = $('#mcpSelected');
  wrap.innerHTML = '';
  const mcp = SETTINGS.mcp || {};
  const pills = [];
  if (mcp.github?.enabled) {
    const label = mcp.github.repo ? `GitHub Issues (${mcp.github.repo})` : 'GitHub Issues';
    pills.push(label);
  }
  if (mcp.postgres?.enabled) {
    pills.push('PostgreSQL');
  }
  wrap.innerHTML = pills.length
    ? pills.map(t => `<span class="pill">${htmlEscape(t)}</span>`).join(' ')
    : `<span class="text-slate-500 text-sm">No connectors enabled</span>`;
}

/* ----------------------------- Progress Bar Helpers ----------------------------- */

function showProgress(progressId, statusId, progressBarId, textId, buttonId) {
  $(progressId).classList.remove('hidden');
  $(statusId).classList.remove('hidden');
  $(buttonId).disabled = true;
  $(textId).textContent = 'Processing...';
  logDebug('progress.show', { 
    progressId, 
    statusId, 
    progressBarId, 
    textId, 
    buttonId,
    timestamp: new Date().toISOString()
  });
}

function updateProgress(progressBarId, statusId, percent, status) {
  $(progressBarId).style.width = `${percent}%`;
  $(statusId).textContent = status;
  logDebug('progress.update', { 
    progressBarId, 
    statusId, 
    percent, 
    status,
    timestamp: new Date().toISOString()
  });
}

function hideProgress(progressId, statusId, textId, buttonId, originalText) {
  $(progressId).classList.add('hidden');
  $(statusId).classList.add('hidden');
  $(buttonId).disabled = false;
  $(textId).textContent = originalText;
  // Reset progress bar width
  const progressBar = $(progressId).querySelector('div');
  if (progressBar) {
    progressBar.style.width = '0%';
  }
  logDebug('progress.hide', { 
    progressId, 
    statusId, 
    textId, 
    buttonId, 
    originalText,
    timestamp: new Date().toISOString()
  });
}

/* ----------------------------- Actions: optimize & send ----------------------------- */

async function optimize() {
  const userPrompt = $('#userPrompt').value;
  const provider = $('#provider').value || 'anthropic';
  const model = $('#model').value || '';
  
  // Show progress
  showProgress('#optimizeProgress', '#optimizeStatus', '#optimizeProgressBar', '#optimizeText', '#btnOptimize');
  
  try {
    // Simulate progress steps with detailed logging
    logDebug('optimize.start', { userPrompt, provider, model });
    
    updateProgress('#optimizeProgressBar', '#optimizeStatus', 10, 'Fetching GitHub issues...');
    logDebug('optimize.progress', { step: 'fetching_github_issues', percent: 10, status: 'Fetching GitHub issues...' });
    await new Promise(resolve => setTimeout(resolve, 300));
    
    updateProgress('#optimizeProgressBar', '#optimizeStatus', 30, 'Fetching research papers...');
    logDebug('optimize.progress', { step: 'fetching_research_papers', percent: 30, status: 'Fetching research papers...' });
    await new Promise(resolve => setTimeout(resolve, 300));
    
    updateProgress('#optimizeProgressBar', '#optimizeStatus', 50, 'Summarizing content...');
    logDebug('optimize.progress', { step: 'summarizing_content', percent: 50, status: 'Summarizing content...' });
    await new Promise(resolve => setTimeout(resolve, 300));
    
    updateProgress('#optimizeProgressBar', '#optimizeStatus', 70, 'Optimizing prompt...');
    logDebug('optimize.progress', { step: 'optimizing_prompt', percent: 70, status: 'Optimizing prompt...' });
    await new Promise(resolve => setTimeout(resolve, 300));
    
    updateProgress('#optimizeProgressBar', '#optimizeStatus', 80, 'Building request...');
    logDebug('optimize.progress', { step: 'building_request', percent: 80, status: 'Building request...' });
    await new Promise(resolve => setTimeout(resolve, 200));
    
         updateProgress('#optimizeProgressBar', '#optimizeStatus', 85, 'Sending to API...');
     logDebug('optimize.progress', { step: 'sending_to_api', percent: 85, status: 'Sending to API...' });
     
     const requestBody = { user_prompt: userPrompt, provider, model };
     logDebug('optimize.request', { url: '/api/optimize', method: 'POST', body: requestBody });
     
     // Simulate MCP calls progress
     updateProgress('#optimizeProgressBar', '#optimizeStatus', 87, 'Calling GitHub MCP...');
     logDebug('optimize.progress', { step: 'calling_github_mcp', percent: 87, status: 'Calling GitHub MCP...' });
     await new Promise(resolve => setTimeout(resolve, 150));
     
     updateProgress('#optimizeProgressBar', '#optimizeStatus', 89, 'Calling PostgreSQL MCP...');
     logDebug('optimize.progress', { step: 'calling_postgresql_mcp', percent: 89, status: 'Calling PostgreSQL MCP...' });
     await new Promise(resolve => setTimeout(resolve, 150));
     
     updateProgress('#optimizeProgressBar', '#optimizeStatus', 91, 'Sending to LLM...');
     logDebug('optimize.progress', { step: 'sending_to_llm', percent: 91, status: 'Sending to LLM...' });
     
     const res = await fetch('/api/optimize', {
       method:'POST',
       headers:{'Content-Type':'application/json'},
       body: JSON.stringify(requestBody)
     });
    
    updateProgress('#optimizeProgressBar', '#optimizeStatus', 95, 'Processing response...');
    logDebug('optimize.progress', { step: 'processing_response', percent: 95, status: 'Processing response...', statusCode: res.status });
    await new Promise(resolve => setTimeout(resolve, 200));
    
    updateProgress('#optimizeProgressBar', '#optimizeStatus', 100, 'Complete!');
    logDebug('optimize.progress', { step: 'complete', percent: 100, status: 'Complete!' });
    await new Promise(resolve => setTimeout(resolve, 200));
    
    const data = await res.json();
    logDebug('optimize.response', { status: res.status, data: data });
    
    $('#optimizedPrompt').value = data.optimized_prompt || userPrompt;

    // Rich debug
    renderDebug(data.debug);
    logDebug('optimize.success', { optimized_prompt: data.optimized_prompt, debug: data.debug });
    activateTab('debug');
    
  } catch (error) {
    updateProgress('#optimizeProgressBar', '#optimizeStatus', 100, 'Error occurred');
    logDebug('optimize.error', { error: error.message, stack: error.stack });
    console.error('Optimize error:', error);
  } finally {
    // Hide progress after a short delay
    setTimeout(() => {
      hideProgress('#optimizeProgress', '#optimizeStatus', '#optimizeText', '#btnOptimize', 'Summarize → Optimize');
      logDebug('optimize.complete', { finalStatus: 'Progress hidden, operation complete' });
    }, 1000);
  }
}

async function send() {
  const provider = $('#provider').value || 'anthropic';
  const model = $('#model').value || '';
  const userPrompt = $('#userPrompt').value;
  const optimizedPrompt = $('#optimizedPrompt').value || userPrompt;

  // Show progress
  showProgress('#sendProgress', '#sendStatus', '#sendProgressBar', '#sendText', '#btnSend');
  
  try {
    // Simulate progress steps with detailed logging
    logDebug('send.start', { userPrompt, optimizedPrompt, provider, model });
    
    updateProgress('#sendProgressBar', '#sendStatus', 10, 'Fetching fresh data...');
    logDebug('send.progress', { step: 'fetching_fresh_data', percent: 10, status: 'Fetching fresh data...' });
    await new Promise(resolve => setTimeout(resolve, 200));
    
    updateProgress('#sendProgressBar', '#sendStatus', 30, 'Building optimized prompt...');
    logDebug('send.progress', { step: 'building_optimized_prompt', percent: 30, status: 'Building optimized prompt...' });
    await new Promise(resolve => setTimeout(resolve, 200));
    
    updateProgress('#sendProgressBar', '#sendStatus', 50, 'Sending to AI provider...');
    logDebug('send.progress', { step: 'sending_to_ai_provider', percent: 50, status: 'Sending to AI provider...' });
    await new Promise(resolve => setTimeout(resolve, 200));
    
    updateProgress('#sendProgressBar', '#sendStatus', 70, 'Processing response...');
    logDebug('send.progress', { step: 'processing_response', percent: 70, status: 'Processing response...' });
    await new Promise(resolve => setTimeout(resolve, 200));
    
    updateProgress('#sendProgressBar', '#sendStatus', 80, 'Building request...');
    logDebug('send.progress', { step: 'building_request', percent: 80, status: 'Building request...' });
    await new Promise(resolve => setTimeout(resolve, 200));
    
         updateProgress('#sendProgressBar', '#sendStatus', 85, 'Sending to AI provider...');
     logDebug('send.progress', { step: 'sending_to_ai_provider_api', percent: 85, status: 'Sending to AI provider...' });
     
     const requestBody = { provider, model, user_prompt: userPrompt, optimized_prompt: optimizedPrompt };
     logDebug('send.request', { url: '/api/chat', method: 'POST', body: requestBody });
     
     // Simulate MCP calls progress
     updateProgress('#sendProgressBar', '#sendStatus', 87, 'Calling GitHub MCP...');
     logDebug('send.progress', { step: 'calling_github_mcp', percent: 87, status: 'Calling GitHub MCP...' });
     await new Promise(resolve => setTimeout(resolve, 150));
     
     updateProgress('#sendProgressBar', '#sendStatus', 89, 'Calling PostgreSQL MCP...');
     logDebug('send.progress', { step: 'calling_postgresql_mcp', percent: 89, status: 'Calling PostgreSQL MCP...' });
     await new Promise(resolve => setTimeout(resolve, 150));
     
     updateProgress('#sendProgressBar', '#sendStatus', 91, 'Sending to LLM...');
     logDebug('send.progress', { step: 'sending_to_llm', percent: 91, status: 'Sending to LLM...' });
     
     const res = await fetch('/api/chat', {
       method:'POST',
       headers:{'Content-Type':'application/json'},
       body: JSON.stringify(requestBody)
     });
    
    updateProgress('#sendProgressBar', '#sendStatus', 95, 'Parsing response...');
    logDebug('send.progress', { step: 'parsing_response', percent: 95, status: 'Parsing response...', statusCode: res.status });
    await new Promise(resolve => setTimeout(resolve, 200));
    
    updateProgress('#sendProgressBar', '#sendStatus', 100, 'Complete!');
    logDebug('send.progress', { step: 'complete', percent: 100, status: 'Complete!' });
    await new Promise(resolve => setTimeout(resolve, 200));
    
    const data = await res.json();
    logDebug('send.response', { status: res.status, data: data });

    const convo = $('#conversation');
    const userDiv = document.createElement('div');
    userDiv.className="p-2 rounded bg-slate-100";
    userDiv.textContent = userPrompt;
    const botDiv = document.createElement('div');
    botDiv.className="p-2 rounded bg-blue-50";
    botDiv.textContent = data.structured || data.text || "(no response)";
    convo.appendChild(userDiv);
    convo.appendChild(botDiv);
    convo.scrollTop = convo.scrollHeight;

    logDebug('send.conversation', { 
      userMessage: userPrompt, 
      botResponse: data.structured || data.text || "(no response)",
      conversationLength: convo.children.length 
    });

    // Rich debug
    renderDebug(data.debug);
    logDebug('send.success', { 
      structured: data.structured, 
      text: data.text, 
      debug: data.debug 
    });
    activateTab('debug');
    
  } catch (error) {
    updateProgress('#sendProgressBar', '#sendStatus', 100, 'Error occurred');
    logDebug('send.error', { error: error.message, stack: error.stack });
    console.error('Send error:', error);
  } finally {
    // Hide progress after a short delay
    setTimeout(() => {
      hideProgress('#sendProgress', '#sendStatus', '#sendText', '#btnSend', 'Send');
      logDebug('send.complete', { finalStatus: 'Progress hidden, operation complete' });
    }, 1000);
  }
}

/* ----------------------------- Init ----------------------------- */

function bindUI() {
  $$('.tab').forEach(b => b.addEventListener('click', () => activateTab(b.dataset.tab)));
  $('#settingsForm').addEventListener('submit', saveSettingsFromForm);
  $('#btnOptimize').addEventListener('click', optimize);
  $('#btnSend').addEventListener('click', send);
  bindPromptTemplateUI();
  
  // Research Paper Workflow Example Prompts
  $('#btnExample1').addEventListener('click', () => {
    $('#userPrompt').value = `I need to build a recommendation system for e-commerce. What research papers and GitHub issues are relevant to this project? Please provide:
1. Key research papers on recommendation systems
2. Relevant GitHub issues that might inform the implementation
3. Implementation guidance based on the research findings`;
  });
  
  $('#btnExample2').addEventListener('click', () => {
    $('#userPrompt').value = `Extract project requirements from GitHub issues and match them with relevant AI research papers. Focus on:
1. Technical specifications and implementation needs
2. Research papers that address similar requirements
3. Gap analysis between requirements and available research`;
  });
  
  $('#btnExample3').addEventListener('click', () => {
    $('#userPrompt').value = `Based on the GitHub issues and research papers, provide implementation guidance for building an AI-powered system. Include:
1. Recommended approaches from research papers
2. Technical architecture suggestions
3. Potential challenges and solutions`;
  });
}

document.addEventListener('DOMContentLoaded', async () => {
  bindUI();
  await loadSettings();
  activateTab('chat');
});
