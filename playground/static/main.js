const $ = sel => document.querySelector(sel);
const $$ = sel => [...document.querySelectorAll(sel)];

let SETTINGS = null;
let DEBUG = [];

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
];

const MODEL_OPTIONS = {
  openai: ["gpt-5", "gpt-4o", "o4-mini"],
  anthropic: ["claude-4-sonnet", "claude-3.7-sonnet", "claude-3.5-sonnet"],
  ollama: ["gemma3:270m", "gpt-oss:20b", "llama3.2:3b"],
  google: ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"],
};

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



function logDebug(section, obj) {
  DEBUG.push({ ts: new Date().toISOString(), section, obj });
  $('#debugLog').textContent = JSON.stringify(DEBUG, null, 2);
}

function activateTab(name) {
  $$('.tab').forEach(b => b.classList.remove('tab-active'));
  const tabBtn = $(`.tab[data-tab="${name}"]`);
  if (tabBtn) tabBtn.classList.add('tab-active');
  ['chat','debug','settings','templates'].forEach(id => {
    const el = $('#tab-' + id);
    if (el) el.classList.toggle('hidden', id !== name);
  });
}


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
    ? pills.map(t => `<span class="pill">${t}</span>`).join(' ')
    : `<span class="text-slate-500 text-sm">No connectors enabled</span>`;
}

async function optimize() {
  const userPrompt = $('#userPrompt').value;
  const provider = $('#provider').value || 'anthropic';
  const model = $('#model').value || '';
  const res = await fetch('/api/optimize', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ user_prompt: userPrompt, provider, model })
  });
  const data = await res.json();
  $('#optimizedPrompt').value = data.optimized_prompt || userPrompt;
  logDebug('optimize', data.debug);
  activateTab('debug');
}

async function send() {
  const provider = $('#provider').value || 'anthropic';
  const model = $('#model').value || '';
  const userPrompt = $('#userPrompt').value;
  const optimizedPrompt = $('#optimizedPrompt').value || userPrompt;
  const res = await fetch('/api/chat', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ provider, model, user_prompt: userPrompt, optimized_prompt: optimizedPrompt })
  });
  const data = await res.json();

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

  logDebug('chat', data.debug);
  activateTab('debug');
}

function bindUI() {
  $$('.tab').forEach(b => b.addEventListener('click', () => activateTab(b.dataset.tab)));
  $('#settingsForm').addEventListener('submit', saveSettingsFromForm);
  $('#btnOptimize').addEventListener('click', optimize);
  $('#btnSend').addEventListener('click', send);
  bindPromptTemplateUI();
}

document.addEventListener('DOMContentLoaded', async () => {
  bindUI();
  await loadSettings();
  activateTab('chat');
});
