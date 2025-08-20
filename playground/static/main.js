const $ = sel => document.querySelector(sel);
const $$ = sel => [...document.querySelectorAll(sel)];

let SETTINGS = null;
let DEBUG = [];

// Known models for dropdowns
const MODEL_OPTIONS = {
  openai: ["gpt-5", "gpt-4o", "o4-mini"],
  anthropic: ["claude-4-sonnet", "claude-3.7-sonnet", "claude-3.5-sonnet"],
  ollama: ["gemma3:270m", "gpt-oss:20b", "llama3.2:3b"],
  google: ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"],
};

function logDebug(section, obj) {
  DEBUG.push({ ts: new Date().toISOString(), section, obj });
  $('#debugLog').textContent = JSON.stringify(DEBUG, null, 2);
}

function activateTab(name) {
  $$('.tab').forEach(b => b.classList.remove('tab-active'));
  $(`.tab[data-tab="${name}"]`).classList.add('tab-active');
  ['chat','debug','settings'].forEach(id => {
    $('#tab-' + id).classList.toggle('hidden', id !== name);
  });
}

async function loadSettings() {
  const res = await fetch('/api/settings');
  SETTINGS = await res.json();
  fillSettingsFormFromSettings();
  fillProviderDropdownFromSettings();
  renderMcpSelected();
}

function ensureOption(selectEl, value, label) {
  if (![...selectEl.options].some(o => o.value === value)) {
    const opt = document.createElement('option');
    opt.value = value; opt.textContent = label || value;
    selectEl.appendChild(opt);
  }
}

function populateModelSelect(selectEl, providerKey, defaultVal) {
  selectEl.innerHTML = '';
  const options = MODEL_OPTIONS[providerKey] || [];
  options.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m; opt.textContent = m;
    selectEl.appendChild(opt);
  });
  if (defaultVal) ensureOption(selectEl, defaultVal, defaultVal);
  selectEl.value = defaultVal || options[0] || '';
}

function fillProviderDropdownFromSettings() {
  const provSel = $('#provider');
  const modelSel = $('#model');
  provSel.innerHTML = '';
  const providers = SETTINGS.providers || {};

  // Add enabled providers
  Object.entries(providers).forEach(([key, p]) => {
    if (p.enabled) {
      const opt = document.createElement('option');
      opt.value = key;
      opt.textContent = `${p.name} (${key})`;
      provSel.appendChild(opt);
    }
  });

  // Default selection rule: prefer Anthropic if enabled
  let chosen = 'anthropic';
  if (!(providers.anthropic && providers.anthropic.enabled)) {
    const first = provSel.options[0];
    chosen = first ? first.value : chosen;
  }
  provSel.value = chosen;

  // Populate model dropdown for chosen provider
  const defaultModel = providers[chosen]?.default_model || '';
  populateModelSelect(modelSel, chosen, defaultModel);

  // Change handler keeps model dropdown in sync
  provSel.addEventListener('change', () => {
    const k = provSel.value;
    const defModel = providers[k]?.default_model || '';
    populateModelSelect(modelSel, k, defModel);
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

  // Anthropic (enabled default)
  $('#anthropic_enabled').checked = p.anthropic.enabled;
  $('#anthropic_url').value = p.anthropic.base_url;
  $('#anthropic_key').value = p.anthropic.api_key;
  populateModelSelect($('#anthropic_model'), 'anthropic', p.anthropic.default_model);
  $('#anthropic_temp').value = p.anthropic.temperature;

  // Ollama
  $('#ollama_enabled').checked = p.ollama.enabled;
  $('#ollama_url').value = p.ollama.base_url;
  populateModelSelect($('#ollama_model'), 'ollama', p.ollama.default_model);
  $('#ollama_temp').value = p.ollama.temperature;

  // Google
  $('#google_enabled').checked = p.google.enabled;
  $('#google_url').value = p.google.base_url;
  $('#google_key').value = p.google.api_key;
  populateModelSelect($('#google_model'), 'google', p.google.default_model);
  $('#google_temp').value = p.google.temperature;

  // MCP connectors (pre-selected by default per requirement)
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
  const payload = {
    providers: {
      openai: {
        enabled: $('#openai_enabled').checked, name: 'OpenAI',
        base_url: $('#openai_url').value, api_key: $('#openai_key').value,
        default_model: $('#openai_model').value, temperature: parseFloat($('#openai_temp').value || '0.2'),
      },
      anthropic: {
        enabled: $('#anthropic_enabled').checked, name: 'Anthropic',
        base_url: $('#anthropic_url').value, api_key: $('#anthropic_key').value,
        default_model: $('#anthropic_model').value, temperature: parseFloat($('#anthropic_temp').value || '0.2'),
      },
      ollama: {
        enabled: $('#ollama_enabled').checked, name: 'Ollama',
        base_url: $('#ollama_url').value, api_key: '',
        default_model: $('#ollama_model').value, temperature: parseFloat($('#ollama_temp').value || '0.2'),
      },
      google: {
        enabled: $('#google_enabled').checked, name: 'Google',
        base_url: $('#google_url').value, api_key: $('#google_key').value,
        default_model: $('#google_model').value, temperature: parseFloat($('#google_temp').value || '0.2'),
      },
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
  await loadSettings(); // re-sync Chat tab provider+model and MCP selected list
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
  if (pills.length === 0) {
    wrap.innerHTML = `<span class="text-slate-500 text-sm">No connectors enabled</span>`;
    return;
  }
  pills.forEach(t => {
    const span = document.createElement('span');
    span.className = 'pill';
    span.textContent = t;
    wrap.appendChild(span);
  });
}

// Optimize & Send
async function optimize() {
  const userPrompt = $('#userPrompt').value;
  const res = await fetch('/api/optimize', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ user_prompt: userPrompt }) });
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
}

document.addEventListener('DOMContentLoaded', async () => {
  bindUI();
  await loadSettings();
  activateTab('chat');
});
