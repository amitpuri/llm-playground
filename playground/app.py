import os, json, textwrap, requests, asyncio
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify

# Optional: pip install fastmcp
try:
    from fastmcp import Client as MCPClient
    from fastmcp.client.auth import BearerAuth as MCPBearerAuth
except Exception:
    MCPClient = None
    MCPBearerAuth = None

load_dotenv()

app = Flask(__name__)
SETTINGS_PATH = os.getenv("PLAYGROUND_SETTINGS_PATH", "settings.json")

# ----------------------------- Settings Model -----------------------------

@dataclass
class ProviderConf:
    enabled: bool = False
    name: str = ""
    base_url: str = ""
    api_key: str = ""
    temperature: float = 0.2
    default_model: str = ""

@dataclass
class MCPGitHubConf:
    enabled: bool = False
    url: str = ""
    auth_token: str = ""
    repo: str = ""

@dataclass
class MCPPostgresConf:
    enabled: bool = False
    url: str = ""
    auth_token: str = ""
    sample_sql: str = "SELECT * from research_papers.ai_research_papers;"

@dataclass
class AppSettings:
    providers: Dict[str, ProviderConf]
    mcp: Dict[str, Any]

DEFAULT_SETTINGS = AppSettings(
    providers={
        "openai": ProviderConf(
            enabled=False,
            name="OpenAI",
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            api_key=os.getenv("OPENAI_API_KEY", ""),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
            default_model=os.getenv("OPENAI_DEFAULT_MODEL", "gpt-5"),
        ),
        # Anthropic ON by default
        "anthropic": ProviderConf(
            enabled=True,
            name="Anthropic",
            base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.2")),
            default_model=os.getenv("ANTHROPIC_DEFAULT_MODEL", "claude-4-sonnet"),
        ),
        # Ollama ON (optimizer uses gemma3:270m)
        "ollama": ProviderConf(
            enabled=True,
            name="Ollama",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            api_key="",
            temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.2")),
            default_model=os.getenv("OLLAMA_DEFAULT_MODEL", "gemma3:270m"),
        ),
        # NEW: Google Gemini provider
        "google": ProviderConf(
            enabled=False,
            name="Google",
            base_url=os.getenv("GOOGLE_BASE_URL", "https://generativelanguage.googleapis.com"),
            api_key=os.getenv("GOOGLE_API_KEY", ""),
            temperature=float(os.getenv("GOOGLE_TEMPERATURE", "0.2")),
            default_model=os.getenv("GOOGLE_DEFAULT_MODEL", "gemini-2.5-pro"),
        ),
    },
    mcp={
        # MCP connectors selected by default
        "github": asdict(MCPGitHubConf(
            enabled=True,
            url=os.getenv("MCP_SERVER_URL", "https://api.githubcopilot.com/mcp/"),
            auth_token=os.getenv("GITHUB_TOKEN", ""),
            repo=os.getenv("GITHUB_REPO", "owner/repo"),
        )),
        "postgres": asdict(MCPPostgresConf(
            enabled=True,
            url=os.getenv("MCP_SSE_SERVER_URL", "http://localhost:8000/sse"),
            auth_token=os.getenv("MCP_AUTH_TOKEN", ""),
            sample_sql=os.getenv("PG_SAMPLE_SQL", "SELECT * from research_papers.ai_research_papers;"),
        )),
    }
)

def _deep_merge(dst, src):
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_merge(dst[k], v)
        else:
            dst[k] = v

def load_settings() -> AppSettings:
    if not os.path.exists(SETTINGS_PATH):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    cur = json.loads(json.dumps(asdict(DEFAULT_SETTINGS)))
    _deep_merge(cur, raw)
    prov = {k: ProviderConf(**v) for k, v in cur["providers"].items()}
    return AppSettings(providers=prov, mcp=cur["mcp"])

def save_settings(s: AppSettings):
    data = {"providers": {k: asdict(v) for k, v in s.providers.items()}, "mcp": s.mcp}
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ----------------------------- MCP helpers -----------------------------

def _mcp_connect(url: str, token: Optional[str]):
    if MCPClient is None:
        raise RuntimeError("fastmcp not installed. pip install fastmcp")
    auth = MCPBearerAuth(token) if token else None
    return MCPClient(url, auth=auth)

def _jsonify_tc(payload: Any) -> Any:
    data = getattr(payload, "content", payload)
    if isinstance(data, dict) and "content" in data:
        data = data["content"]
    def is_tc(x): return hasattr(x, "text") and isinstance(getattr(x, "text"), str)
    if isinstance(data, list) and data and is_tc(data[0]):
        txt = "".join(getattr(tc, "text", "") for tc in data if is_tc(tc))
        try: return json.loads(txt)
        except Exception: return txt
    if is_tc(data):
        try: return json.loads(data.text)
        except Exception: return data.text
    return data

async def mcp_github_context(conf: MCPGitHubConf) -> Tuple[str, Dict[str, Any]]:
    debug = {"tools": [], "issues_raw": None}
    if not conf.enabled or not conf.url or not conf.repo:
        return "", {"error": "github_mcp_disabled_or_not_configured"}
    owner_repo = conf.repo.strip()
    if "/" not in owner_repo:
        return "", {"error": "GITHUB repo must be owner/repo"}
    owner, repo = owner_repo.split("/", 1)
    async with _mcp_connect(conf.url, conf.auth_token) as client:
        tools = await client.list_tools()
        debug["tools"] = [getattr(t, "name", None) or t.get("name") for t in tools]
        names = set(debug["tools"])
        issues = []
        try:
            if "search_issues" in names:
                raw = await client.call_tool("search_issues", {"query": f"repo:{owner}/{repo} is:issue is:open", "page": 1, "per_page": 10})
                doc = _jsonify_tc(raw)
                if isinstance(doc, dict) and "items" in doc: issues = doc["items"]
                elif isinstance(doc, list): issues = doc
            elif "list_issues" in names:
                raw = await client.call_tool("list_issues", {"owner": owner, "repo": repo, "state": "open", "page": 1, "per_page": 10})
                doc = _jsonify_tc(raw)
                if isinstance(doc, list): issues = doc
        except Exception as e:
            debug["issues_error"] = str(e)
    debug["issues_raw"] = issues
    lines = []
    for it in (issues or [])[:5]:
        title = it.get("title"); num = it.get("number", ""); st = (it.get("state") or "").lower()
        lines.append(f"- Issue #{num} [{st}]: {title}")
    txt = "GitHub Issues Context:\n" + ("\n".join(lines) if lines else "No open issues.")
    return txt.strip(), debug

async def mcp_postgres_context(conf: MCPPostgresConf) -> Tuple[str, Dict[str, Any]]:
    debug = {"tools": [], "result_raw": None}
    if not conf.enabled or not conf.url:
        return "", {"error": "postgres_mcp_disabled_or_not_configured"}
    sql = (conf.sample_sql or "SELECT * from research_papers.ai_research_papers;").strip()
    async with _mcp_connect(conf.url, conf.auth_token) as client:
        tools = await client.list_tools()
        debug["tools"] = [getattr(t, "name", None) or t.get("name") for t in tools]
        try:
            raw = await client.call_tool("execute_sql", {"sql": sql})
            doc = _jsonify_tc(raw)
            debug["result_raw"] = doc
            if isinstance(doc, list) and doc:
                s = json.dumps(doc[0], ensure_ascii=False)[:300]
            elif isinstance(doc, dict):
                s = json.dumps(doc, ensure_ascii=False)[:300]
            else:
                s = str(doc)[:300]
            txt = f"PostgreSQL Context (first result): {s}"
            return txt, debug
        except Exception as e:
            debug["error"] = str(e)
            return "PostgreSQL Context: <error>", debug

# ----------------------------- Model calls -----------------------------

def call_ollama(base_url: str, model: str, prompt: str, temperature: float = 0.2) -> str:
    url = f"{base_url.rstrip('/')}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False, "options": {"temperature": temperature}}
    r = requests.post(url, json=payload, timeout=120)
    r.raise_for_status()
    return r.json().get("response", "").strip()

def call_openai(base_url: str, api_key: str, model: str, system: str, user: str, temperature: float = 0.2) -> str:
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "temperature": temperature,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

def call_anthropic(base_url: str, api_key: str, model: str, system: str, user: str, temperature: float = 0.2) -> str:
    url = f"{base_url.rstrip('/')}/v1/messages"
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    payload = {"model": model, "max_tokens": 2048, "temperature": temperature, "system": system, "messages": [{"role": "user", "content": user}]}
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    out = ""
    for b in data.get("content", []):
        if b.get("type") == "text":
            out += b.get("text", "")
    return out.strip()

# NEW: Google Gemini (Generative Language API)
def call_google(base_url: str, api_key: str, model: str, system: str, user: str, temperature: float = 0.2) -> str:
    # POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key=API_KEY
    endpoint = f"{base_url.rstrip('/')}/v1beta/models/{model}:generateContent"
    params = {"key": api_key} if api_key else {}
    text = f"{system}\n\n{user}".strip()
    payload = {
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        "generationConfig": {"temperature": temperature},
    }
    r = requests.post(endpoint, params=params, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    # Extract first text
    try:
        parts = data["candidates"][0]["content"]["parts"]
        combined = "".join(p.get("text", "") for p in parts)
        return combined.strip()
    except Exception:
        return json.dumps(data)[:2000]  # fallback raw if unexpected

STRUCT_SCHEMA = textwrap.dedent("""
Return ONLY valid JSON with keys:
{
  "answer": string,
  "used_connectors": string[],
  "citations": string[]
}
""").strip()

OPTIMIZER_SYSTEM = "You are a prompt optimizer. Rewrite user intent + MCP context into a concise, actionable prompt."
PROVIDER_SYSTEM  = "You are a helpful assistant that replies ONLY with the JSON specified schema."

def build_optimized_prompt(user_prompt: str, mcp_context_text: str, ollama_conf: ProviderConf) -> Tuple[str, Dict[str, Any]]:
    dbg = {"optimizer_model": ollama_conf.default_model, "optimizer_base": ollama_conf.base_url}
    if not ollama_conf.enabled:
        return user_prompt, {**dbg, "note": "Ollama disabled; using user prompt"}
    try:
        prompt = f"""User request:
{user_prompt}

MCP context:
{mcp_context_text}

Task: Create an improved prompt that will help an LLM answer the user request using the given context. Keep it short."""
        out = call_ollama(ollama_conf.base_url, "gemma3:270m", prompt, temperature=ollama_conf.temperature)
        return (out or user_prompt), {**dbg, "optimizer_prompt": prompt, "optimizer_output": out}
    except Exception as e:
        return user_prompt, {**dbg, "optimizer_error": str(e)}

def call_provider(provider_key: str, settings: AppSettings, model: Optional[str], final_prompt: str) -> Tuple[str, Dict[str, Any]]:
    p = settings.providers.get(provider_key)
    if not p or not p.enabled:
        raise RuntimeError(f"Provider '{provider_key}' disabled or not configured")
    model = model or p.default_model
    sys_prompt = f"{PROVIDER_SYSTEM}\n\nSchema:\n{STRUCT_SCHEMA}"
    dbg = {"provider": provider_key, "model": model, "base_url": p.base_url}
    try:
        if provider_key == "openai":
            out = call_openai(p.base_url, p.api_key, model, sys_prompt, final_prompt, p.temperature)
        elif provider_key == "anthropic":
            out = call_anthropic(p.base_url, p.api_key, model, sys_prompt, final_prompt, p.temperature)
        elif provider_key == "ollama":
            prompt = f"{sys_prompt}\n\nUser:\n{final_prompt}\n\nRespond with JSON only."
            out = call_ollama(p.base_url, model, prompt, p.temperature)
        elif provider_key == "google":
            out = call_google(p.base_url, p.api_key, model, sys_prompt, final_prompt, p.temperature)
        else:
            raise RuntimeError(f"Unknown provider: {provider_key}")

        txt = out.strip()
        if txt.startswith("```"):
            txt = txt.strip("` \n")
            if "\n" in txt:
                txt = txt.split("\n", 1)[1]
        return txt, {**dbg, "raw_output": out}
    except Exception as e:
        return json.dumps({"answer": f"Provider error: {e}", "used_connectors": [], "citations": []}), {**dbg, "error": str(e)}

# ----------------------------- Views -----------------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.get("/api/settings")
def api_get_settings():
    s = load_settings()
    return jsonify({
        "providers": {k: asdict(v) for k, v in s.providers.items()},
        "mcp": s.mcp
    })

@app.post("/api/settings")
def api_set_settings():
    data = request.get_json(force=True)
    cur = load_settings()
    if "providers" in data:
        for k, v in data["providers"].items():
            if k in cur.providers:
                cur.providers[k] = ProviderConf(**{**asdict(cur.providers[k]), **v})
            else:
                cur.providers[k] = ProviderConf(**v)
    if "mcp" in data:
        cur.mcp.update(data["mcp"])
    save_settings(cur)
    return jsonify({"ok": True})

@app.post("/api/optimize")
def api_optimize():
    s = load_settings()
    user_prompt = (request.json.get("user_prompt") or "").strip()

    gh_conf = MCPGitHubConf(**s.mcp["github"])
    pg_conf = MCPPostgresConf(**s.mcp["postgres"])

    mcp_chunks, dbg = [], {"github": None, "postgres": None, "optimizer": None}
    try:
        if gh_conf.enabled:
            txt, info = asyncio.run(mcp_github_context(gh_conf))
            mcp_chunks.append(txt)
            dbg["github"] = info
        if pg_conf.enabled:
            txt, info = asyncio.run(mcp_postgres_context(pg_conf))
            mcp_chunks.append(txt)
            dbg["postgres"] = info
    except Exception as e:
        dbg["mcp_error"] = str(e)

    mcp_text = "\n\n".join([c for c in mcp_chunks if c])
    optimized, opt_dbg = build_optimized_prompt(user_prompt, mcp_text, s.providers["ollama"])
    dbg["optimizer"] = opt_dbg
    return jsonify({"optimized_prompt": optimized, "debug": dbg})

@app.post("/api/chat")
def api_chat():
    s = load_settings()
    provider = request.json.get("provider", "anthropic")  # Anthropic default
    model = request.json.get("model") or None
    user_prompt = (request.json.get("user_prompt") or "").strip()
    optimized_prompt = (request.json.get("optimized_prompt") or "").strip() or user_prompt

    debug: Dict[str, Any] = {"provider": provider, "user_prompt": user_prompt, "optimized_prompt": optimized_prompt}
    txt, pdbg = call_provider(provider, s, model, optimized_prompt)
    debug["provider_io"] = pdbg

    try:
        structured = json.loads(txt)
    except Exception:
        structured = {"answer": txt, "used_connectors": [], "citations": []}

    return jsonify({
        "text": txt,
        "structured": json.dumps(structured, ensure_ascii=False, indent=2),
        "debug": debug
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5050")), debug=True)
