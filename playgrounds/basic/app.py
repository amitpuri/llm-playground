import os, json, textwrap, requests, asyncio, math, re
from typing import Any, Dict, Optional, Tuple, List
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
SETTINGS_PATH = os.getenv("PLAYGROUND_SETTINGS_PATH", "../session-data/settings.json")

# ----------------------------- Settings Model -----------------------------

@dataclass
class ProviderConf:
    enabled: bool = False
    name: str = ""
    base_url: str = ""
    api_key: str = ""
    temperature: float = 0.2
    default_model: str = ""
    context_window: int = 128000  # tokens
    max_completion_tokens: int = 8192
    usage_cap_tokens: int = 1000000
    usage_tracking: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.usage_tracking is None:
            self.usage_tracking = {
                "total_tokens_used": 0,
                "user_tokens": 0,
                "optimized_tokens": 0,
                "response_tokens": 0,
                "api_calls": 0,
                "last_updated": ""
            }

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
    sample_sql: str = "SELECT NOW() AS server_time;"

@dataclass
class OptimizerConf:
    provider: str = "ollama"          # one of: openai | anthropic | ollama | google
    model: str = "gemma3:270m"        # model used for summarizing + optimizing
    temperature: float = 0.2
    max_tokens: int = 1000
    max_context_usage: float = 0.8

@dataclass
class AppSettings:
    providers: Dict[str, ProviderConf]
    mcp: Dict[str, Any]
    optimizer: OptimizerConf
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppSettings':
        """Create AppSettings from dictionary data."""
        providers = {k: ProviderConf(**v) for k, v in data.get("providers", {}).items()}
        optimizer = OptimizerConf(**data.get("optimizer", {}))
        return cls(
            providers=providers,
            mcp=data.get("mcp", {}),
            optimizer=optimizer
        )

DEFAULT_SETTINGS = AppSettings(
    providers={
        "openai": ProviderConf(
            enabled=False,
            name="OpenAI",
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            api_key=os.getenv("OPENAI_API_KEY", ""),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
            default_model=os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o"),
            context_window=int(os.getenv("OPENAI_CONTEXT_WINDOW", "128000")),
            max_completion_tokens=int(os.getenv("OPENAI_MAX_COMPLETION_TOKENS", "8192")),
            usage_cap_tokens=int(os.getenv("OPENAI_USAGE_CAP_TOKENS", "1000000")),
        ),
        "anthropic": ProviderConf(  # enabled by default
            enabled=True,
            name="Anthropic",
            base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.2")),
            default_model=os.getenv("ANTHROPIC_DEFAULT_MODEL", "claude-3-7-sonnet-latest"),
            context_window=int(os.getenv("ANTHROPIC_CONTEXT_WINDOW", "200000")),
            max_completion_tokens=int(os.getenv("ANTHROPIC_MAX_COMPLETION_TOKENS", "8192")),
            usage_cap_tokens=int(os.getenv("ANTHROPIC_USAGE_CAP_TOKENS", "500000")),
        ),
        "ollama": ProviderConf(  # local small model often best for fast summarize
            enabled=True,
            name="Ollama",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            api_key="",
            temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.2")),
            default_model=os.getenv("OLLAMA_DEFAULT_MODEL", "gemma3:270m"),
            context_window=int(os.getenv("OLLAMA_CONTEXT_WINDOW", "8000")),
            max_completion_tokens=int(os.getenv("OLLAMA_MAX_COMPLETION_TOKENS", "4096")),
            usage_cap_tokens=int(os.getenv("OLLAMA_USAGE_CAP_TOKENS", "1000000")),
        ),
        "google": ProviderConf(
            enabled=False,
            name="Google",
            base_url=os.getenv("GOOGLE_BASE_URL", "https://generativelanguage.googleapis.com"),
            api_key=os.getenv("GOOGLE_API_KEY", ""),
            temperature=float(os.getenv("GOOGLE_TEMPERATURE", "0.2")),
            default_model=os.getenv("GOOGLE_DEFAULT_MODEL", "gemini-2.5-pro"),
            context_window=int(os.getenv("GOOGLE_CONTEXT_WINDOW", "128000")),
            max_completion_tokens=int(os.getenv("GOOGLE_MAX_COMPLETION_TOKENS", "8192")),
            usage_cap_tokens=int(os.getenv("GOOGLE_USAGE_CAP_TOKENS", "1000000")),
        ),
    },
    mcp={
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
            sample_sql=os.getenv("PG_SAMPLE_SQL",
                "SELECT url, title, date, abstract, category "
                "FROM research_papers.ai_research_papers "
                "ORDER BY date DESC LIMIT 5;"
            ),
        )),
    },
    optimizer=OptimizerConf(
        provider=os.getenv("OPT_PROVIDER", "anthropic"),   # default to Anthropic
        model=os.getenv("OPT_MODEL", "claude-3-7-sonnet-latest"),
        temperature=float(os.getenv("OPT_TEMPERATURE", "0.2")),
        max_tokens=int(os.getenv("OPT_MAX_TOKENS", "1000")),
        max_context_usage=float(os.getenv("OPT_MAX_CONTEXT_USAGE", "0.8")),
    ),
)

# ----------------------------- Util -----------------------------

import time

def _snip(obj: Any, n: int = 1200) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False)[:n]
    except Exception:
        return str(obj)[:n]

def _snip_text(s: str, n: int = 1200) -> str:
    return (s or "")[:n]

def _call_and_log(calls: List[Dict[str, Any]]):
    """
    Returns a wrapper (tool, args, coro) -> (res, norm)
    that times and logs input/output for MCP tools.
    """
    async def _inner(client, tool: str, args: Dict[str, Any], coro):
        t0 = time.perf_counter()
        entry = {"tool": tool, "input": args}
        try:
            res = await coro
            norm = _jsonify_tc(res)
            entry.update({
                "ok": True,
                "duration_ms": int((time.perf_counter() - t0) * 1000),
                "output_preview": _snip(norm),
            })
            calls.append(entry)
            return res, norm
        except Exception as e:
            entry.update({
                "ok": False,
                "duration_ms": int((time.perf_counter() - t0) * 1000),
                "error": str(e),
            })
            calls.append(entry)
            raise
    return _inner


def _deep_merge(dst, src):
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_merge(dst[k], v)
        else:
            dst[k] = v

def load_settings() -> AppSettings:
    """Load settings from JSON file with fallback to sample.settings.json."""
    # Try to load from the specified file path first
    if os.path.exists(SETTINGS_PATH):
        print(f"Loading settings from: {SETTINGS_PATH}")
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        return AppSettings.from_dict(raw_data)
    
    # If the specified file doesn't exist, try to use sample.settings.json as template
    sample_path = "../sample.settings.json"
    if os.path.exists(sample_path):
        print(f"settings.json not found, loading from: {sample_path}")
        with open(sample_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        settings = AppSettings.from_dict(raw_data)
        # Save to the session file to create it
        save_settings(settings)
        return settings
    
    # If neither exists, return default settings
    print("No settings file found, using default settings")
    return DEFAULT_SETTINGS

def save_settings(s: AppSettings):
    data = {
        "providers": {k: asdict(v) for k, v in s.providers.items()},
        "mcp": s.mcp,
        "optimizer": asdict(s.optimizer),
    }
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def est_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))

def trim_to_tokens(text: str, max_tokens: int) -> str:
    if est_tokens(text) <= max_tokens: return text
    return text[: max(0, max_tokens * 4)]

# ----------------------------- MCP helpers -----------------------------

def _mcp_connect(url: str, token: Optional[str]):
    if MCPClient is None:
        raise RuntimeError("fastmcp not installed. pip install fastmcp")
    auth = MCPBearerAuth(token) if token else None
    return MCPClient(url, auth=auth)

def _extract_fenced_json(s: str) -> Optional[str]:
    """
    Extract ```json ... ``` or ``` ... ``` blocks if present.
    Return the inner JSON text or None.
    """
    if not isinstance(s, str):
        return None
    m = re.search(r"```json\s*(.*?)\s*```", s, re.S | re.I)
    if m:
        return m.group(1)
    m = re.search(r"```\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*```", s, re.S)
    if m:
        return m.group(1)
    return None

def _try_json(s: str) -> Optional[Any]:
    try:
        return json.loads(s)
    except Exception:
        return None

def _jsonify_tc(payload: Any) -> Any:
    """
    Normalize fastmcp ToolResult payloads into python objects.
    - Accepts List[TextContent], TextContent, dict, list, or raw strings.
    - Tries: JSON → fenced JSON → lightly 'json-ized' strings → raw.
    """
    data = getattr(payload, "content", payload)
    if isinstance(data, dict) and "content" in data:
        data = data["content"]

    def join_text_chunks(lst):
        parts = []
        for tc in lst:
            t = getattr(tc, "text", None)
            if isinstance(t, str):
                parts.append(t)
        return "\n".join(parts).strip()

    # Case: list of TextContent
    if isinstance(data, list) and data and hasattr(data[0], "text"):
        raw = join_text_chunks(data)
        if not raw:
            return data
        j = _try_json(raw)
        if j is not None:
            return j
        inner = _extract_fenced_json(raw)
        if inner:
            j = _try_json(inner)
            if j is not None:
                return j
        naive = raw.replace("None", "null").replace("True", "true").replace("False", "false")
        naive = re.sub(r"(?<!\\)\'", '"', naive)
        j = _try_json(naive)
        if j is not None:
            return j
        return raw

    # Case: single TextContent
    if hasattr(data, "text") and isinstance(getattr(data, "text"), str):
        raw = data.text
        j = _try_json(raw)
        if j is not None:
            return j
        inner = _extract_fenced_json(raw)
        if inner:
            j = _try_json(inner)
            if j is not None:
                return j
        naive = raw.replace("None", "null").replace("True", "true").replace("False", "false")
        naive = re.sub(r"(?<!\\)\'", '"', naive)
        j = _try_json(naive)
        if j is not None:
            return j
        return raw

    return data

# ----------------------------- Provider calls -----------------------------

def call_ollama(base_url: str, model: str, prompt: str, temperature: float = 0.2) -> str:
    url = f"{base_url.rstrip('/')}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False, "options": {"temperature": temperature}}
    r = requests.post(url, json=payload, timeout=180)
    r.raise_for_status()
    return r.json().get("response", "").strip()

def call_openai(base_url: str, api_key: str, model: str, system: str, user: str, temperature: float = 0.2) -> str:
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model, 
        "max_completion_tokens": 4096,  # Use max_completion_tokens for GPT-5
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
    }
    
    # GPT-5 doesn't support custom temperature, only default (1)
    if not model.startswith("gpt-5"):
        payload["temperature"] = temperature
    
    # Debug logging
    print(f"OpenAI API Call Debug:")
    print(f"  URL: {url}")
    print(f"  Model: {model}")
    print(f"  API Key (first 10 chars): {api_key[:10]}...")
    print(f"  Payload keys: {list(payload.keys())}")
    print(f"  Messages count: {len(payload['messages'])}")
    
    r = requests.post(url, headers=headers, json=payload, timeout=180)
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        body = ""
        try:
            body = r.text[:2000]
        except Exception:
            pass
        print(f"OpenAI API Error:")
        print(f"  Status Code: {r.status_code}")
        print(f"  Response Headers: {dict(r.headers)}")
        print(f"  Response Body: {body}")
        raise requests.HTTPError(f"OpenAI API Error {r.status_code}: {e} :: {body}") from None
    return r.json()["choices"][0]["message"]["content"].strip()

def _anth_endpoint(base_url: str, resource: str = "messages") -> str:
    b = (base_url or "").rstrip("/")
    if b.endswith("/v1"):
        return f"{b}/{resource.lstrip('/')}"
    return f"{b}/v1/{resource.lstrip('/')}"

def call_anthropic(base_url: str, api_key: str, model: str, system: str, user: str, temperature: float = 0.2) -> str:
    if not api_key:
        raise RuntimeError("Anthropic API key missing")

    url = _anth_endpoint(base_url, "messages")
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": 2048,
        "temperature": temperature,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }

    r = requests.post(url, headers=headers, json=payload, timeout=180)
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        body = ""
        try:
            body = r.text[:2000]
        except Exception:
            pass
        raise requests.HTTPError(f"{e} :: {body}") from None

    data = r.json()
    out = ""
    for b in data.get("content", []):
        if isinstance(b, dict) and b.get("type") == "text":
            out += b.get("text", "")
    return out.strip()


def call_google(base_url: str, api_key: str, model: str, system: str, user: str, temperature: float = 0.2) -> str:
    endpoint = f"{base_url.rstrip('/')}/v1beta/models/{model}:generateContent"
    params = {"key": api_key} if api_key else {}
    text = f"{system}\n\n{user}".strip()
    payload = {"contents": [{"role": "user", "parts": [{"text": text}]}], "generationConfig": {"temperature": temperature}}
    r = requests.post(endpoint, params=params, json=payload, timeout=180)
    r.raise_for_status()
    data = r.json()
    try:
        parts = data["candidates"][0]["content"]["parts"]
        combined = "".join(p.get("text", "") for p in parts)
        return combined.strip()
    except Exception:
        return json.dumps(data)[:2000]

def llm_complete(provider_key: str, prov: ProviderConf, model: str, prompt: str, *, system: Optional[str] = None, temperature: Optional[float] = None) -> str:
    """Unified text completion for optimizer tasks (summaries/instructions)."""
    t = prov.temperature if temperature is None else temperature
    system = system or "You are a helpful assistant."
    if provider_key == "ollama":
        return call_ollama(prov.base_url, model, f"{system}\n\n{prompt}".strip(), t)
    elif provider_key == "openai":
        return call_openai(prov.base_url, prov.api_key, model, system, prompt, t)
    elif provider_key == "anthropic":
        return call_anthropic(prov.base_url, prov.api_key, model, system, prompt, t)
    elif provider_key == "google":
        return call_google(prov.base_url, prov.api_key, model, system, prompt, t)
    else:
        raise RuntimeError(f"Unknown optimizer provider: {provider_key}")

# ----------------------------- Summarizer (configurable) -----------------------------

def summarize_to_tokens_dynamic(
    providers: Dict[str, ProviderConf],
    opt: OptimizerConf,
    text: str,
    target_tokens: int,
) -> str:
    if not text: return text
    p = providers.get(opt.provider)
    if not p or (opt.provider in ("openai", "anthropic", "google") and not p.api_key):
        return trim_to_tokens(text, target_tokens)
    try:
        sys = "You compress content faithfully. Keep concrete facts, IDs, numbers, names. Prefer bullets."
        prompt = f"""Summarize the following to <= {target_tokens} tokens (approx).
Keep key facts, titles, dates, URLs, and short comment insights.

CONTENT:
{text}
"""
        out = llm_complete(opt.provider, p, opt.model, prompt, system=sys, temperature=opt.temperature).strip()
        if est_tokens(out) > target_tokens:
            return trim_to_tokens(out, target_tokens)
        return out
    except Exception:
        return trim_to_tokens(text, target_tokens)

# ----------------------------- GitHub + Postgres fetchers -----------------------------

def parse_model_json(txt: str) -> Dict[str, Any]:
    """
    Accepts raw model text that could be:
    - JSON
    - ```json fenced JSON```
    - top-level JSON whose "answer" contains a fenced JSON block
    Returns a dict with answer/used_connectors/citations.
    """
    s = (txt or "").strip()
    inner = _extract_fenced_json(s)
    if inner:
        s = inner.strip()

    def _as_struct(s2: str) -> Optional[Dict[str, Any]]:
        try:
            obj = json.loads(s2)
        except Exception:
            return None
        if isinstance(obj, dict):
            # If "answer" is a string that itself contains JSON (maybe fenced), parse and prefer it.
            a = obj.get("answer")
            if isinstance(a, str):
                inner2 = _extract_fenced_json(a) or a
                try:
                    nested = json.loads(inner2)
                    if isinstance(nested, dict) and {"answer","used_connectors","citations"} <= set(nested.keys()):
                        return nested
                except Exception:
                    pass
            return obj
        return None

    # Try as-is
    out = _as_struct(s)
    if out is not None:
        return out

    # Try naive JSON-ize
    naive = s.replace("None", "null").replace("True", "true").replace("False", "false")
    naive = re.sub(r"(?<!\\)\'", '"', naive)
    out = _as_struct(naive)
    if out is not None:
        return out

    # Fallback — wrap into schema
    return {"answer": txt, "used_connectors": [], "citations": []}

async def fetch_github_issues_and_comments(conf: MCPGitHubConf, limit_issues: int = 3, limit_comments: int = 5) -> Dict[str, Any]:
    dbg = {"tools": [], "flow": [], "calls": []}
    if not conf.enabled or not conf.url or not conf.repo:
        return {"issues": [], "debug": {**dbg, "error": "github_mcp_disabled_or_not_configured"}}
    owner_repo = conf.repo.strip()
    if "/" not in owner_repo:
        return {"issues": [], "debug": {**dbg, "error": "GITHUB repo must be owner/repo"}}
    owner, repo = owner_repo.split("/", 1)

    items: List[Dict[str, Any]] = []
    async with _mcp_connect(conf.url, conf.auth_token) as client:
        # list_tools (log as a “call” for consistency)
        t0 = time.perf_counter()
        try:
            tools = await client.list_tools()
            dbg["tools"] = [getattr(t, "name", None) or t.get("name") for t in tools]
            dbg["calls"].append({
                "tool": "list_tools",
                "input": {},
                "ok": True,
                "duration_ms": int((time.perf_counter() - t0) * 1000),
                "output_preview": _snip(dbg["tools"]),
            })
        except Exception as e:
            dbg["calls"].append({
                "tool": "list_tools",
                "input": {},
                "ok": False,
                "duration_ms": int((time.perf_counter() - t0) * 1000),
                "error": str(e),
            })
            return {"issues": [], "debug": dbg}

        clog = _call_and_log(dbg["calls"])

        # Prefer search_issues, fall back to list_issues
        if "search_issues" in dbg["tools"]:
            _, doc = await clog(
                client, "search_issues",
                {"query": f"repo:{owner}/{repo} is:issue is:open", "page": 1, "per_page": limit_issues},
                client.call_tool("search_issues", {"query": f"repo:{owner}/{repo} is:issue is:open", "page": 1, "per_page": limit_issues})
            )
            if isinstance(doc, dict) and "items" in doc:
                items = doc["items"][:limit_issues]
            elif isinstance(doc, list):
                items = doc[:limit_issues]
        elif "list_issues" in dbg["tools"]:
            _, doc = await clog(
                client, "list_issues",
                {"owner": owner, "repo": repo, "state": "open", "page": 1, "per_page": limit_issues},
                client.call_tool("list_issues", {"owner": owner, "repo": repo, "state": "open", "page": 1, "per_page": limit_issues})
            )
            if isinstance(doc, list):
                items = doc[:limit_issues]

        dbg["flow"].append({"found_open_issues": len(items)})

        detailed: List[Dict[str, Any]] = []
        for it in items:
            num = it.get("number")
            title = it.get("title")
            state = it.get("state")
            url = it.get("html_url") or it.get("url") or ""
            updated_at = it.get("updated_at") or ""
            labels_in = it.get("labels") or []
            labels = []
            if isinstance(labels_in, list):
                for l in labels_in:
                    labels.append(l.get("name") if isinstance(l, dict) else str(l))

            body = ""
            comments: List[Dict[str, Any]] = []

            if "get_issue" in dbg["tools"] and num is not None:
                _, issue_doc = await clog(
                    client, "get_issue",
                    {"owner": owner, "repo": repo, "issue_number": int(num)},
                    client.call_tool("get_issue", {"owner": owner, "repo": repo, "issue_number": int(num)})
                )
                if isinstance(issue_doc, dict):
                    body = (issue_doc.get("body") or "").strip() or body
                    title = issue_doc.get("title") or title
                    url = issue_doc.get("html_url") or issue_doc.get("url") or url
                    updated_at = issue_doc.get("updated_at") or updated_at
                    lab_src = issue_doc.get("labels")
                    if isinstance(lab_src, list):
                        labels = [ (l.get("name") if isinstance(l, dict) else str(l)) for l in lab_src ]

            if "get_issue_comments" in dbg["tools"] and num is not None:
                _, cm_doc = await clog(
                    client, "get_issue_comments",
                    {"owner": owner, "repo": repo, "issue_number": int(num), "page": 1, "per_page": limit_comments},
                    client.call_tool("get_issue_comments", {"owner": owner, "repo": repo, "issue_number": int(num), "page": 1, "per_page": limit_comments})
                )
                if isinstance(cm_doc, list):
                    for c in cm_doc[:limit_comments]:
                        comments.append({
                            "user": (c.get("user") or {}).get("login", ""),
                            "body": (c.get("body") or "").strip(),
                            "created_at": c.get("created_at", "")
                        })

            detailed.append({
                "number": num, "title": title, "state": state, "url": url,
                "updated_at": updated_at, "labels": labels, "body": body, "comments": comments
            })
        return {"issues": detailed, "debug": dbg}



def _rows_from_doc(doc: Any, limit_rows: int = 8) -> List[Dict[str, Any]]:
    """
    Accepts multiple shapes:
    - list[dict]                         -> rows
    - dict with 'rows' or 'data' list    -> rows
    - string containing JSON array/object -> parsed
    - anything else -> [{"raw": "..."}]
    """
    rows: List[Dict[str, Any]] = []

    if isinstance(doc, list):
        for r in doc[:limit_rows]:
            rows.append(r if isinstance(r, dict) else {"raw": str(r)})
        return rows

    if isinstance(doc, dict):
        if isinstance(doc.get("rows"), list):
            for r in doc["rows"][:limit_rows]:
                rows.append(r if isinstance(r, dict) else {"raw": str(r)})
            return rows
        if isinstance(doc.get("data"), list):
            for r in doc["data"][:limit_rows]:
                rows.append(r if isinstance(r, dict) else {"raw": str(r)})
            return rows
        return [doc]

    if isinstance(doc, str) and doc.strip():
        s = doc.strip()
        inner = _extract_fenced_json(s)
        if inner:
            j = _try_json(inner)
            if j is not None:
                return _rows_from_doc(j, limit_rows)
        j = _try_json(s)
        if j is not None:
            return _rows_from_doc(j, limit_rows)
        naive = s.replace("None", "null").replace("True", "true").replace("False", "false")
        naive = re.sub(r"(?<!\\)\'", '"', naive)
        j = _try_json(naive)
        if j is not None:
            return _rows_from_doc(j, limit_rows)
        return [{"raw": s[:10000]}]

    return rows

async def fetch_research_papers(conf: MCPPostgresConf, limit_rows: int = 8) -> Dict[str, Any]:
    dbg = {"tools": [], "calls": [], "sql": (conf.sample_sql or "SELECT NOW() AS server_time;").strip()}
    if not conf.enabled or not conf.url:
        return {"rows": [], "debug": {**dbg, "error": "postgres_mcp_disabled_or_not_configured"}}

    async with _mcp_connect(conf.url, conf.auth_token) as client:
        # list_tools
        t0 = time.perf_counter()
        try:
            tools = await client.list_tools()
            dbg["tools"] = [getattr(t, "name", None) or t.get("name") for t in tools]
            dbg["calls"].append({
                "tool": "list_tools", "input": {}, "ok": True,
                "duration_ms": int((time.perf_counter() - t0) * 1000),
                "output_preview": _snip(dbg["tools"]),
            })
        except Exception as e:
            dbg["calls"].append({
                "tool": "list_tools", "input": {}, "ok": False,
                "duration_ms": int((time.perf_counter() - t0) * 1000),
                "error": str(e),
            })
            return {"rows": [], "debug": dbg}

        if "execute_sql" not in dbg["tools"]:
            return {"rows": [], "debug": {**dbg, "error": "execute_sql not available"}}

        clog = _call_and_log(dbg["calls"])
        try:
            _, doc = await clog(
                client, "execute_sql", {"sql": dbg["sql"]},
                client.call_tool("execute_sql", {"sql": dbg["sql"]})
            )
            rows = _rows_from_doc(doc, limit_rows)
            return {"rows": rows, "debug": dbg}
        except Exception as e:
            return {"rows": [], "debug": {**dbg, "error": str(e)}}


def render_issues_raw_text(issues: List[Dict[str, Any]]) -> str:
    parts = []
    for it in issues:
        num = it.get("number")
        title = it.get("title") or ""
        url = it.get("url") or ""
        state = it.get("state") or ""
        updated = it.get("updated_at") or ""
        labels = ", ".join([l for l in (it.get("labels") or []) if l]) or "(none)"
        body = (it.get("body") or "").strip()

        parts.append(
            f"Issue #{num}: {title}\n"
            f"URL: {url}\n"
            f"State: {state} | Updated: {updated}\n"
            f"Labels: {labels}\n"
            f"Body:\n{body}"
        )

        cmts = it.get("comments") or []
        if cmts:
            parts.append("Comments:")
            for c in cmts:
                u = c.get("user","")
                b = (c.get("body") or "").strip()
                parts.append(f"- @{u}: {b}")
        parts.append("")
    return "\n".join(parts).strip()

def render_papers_raw_text(rows: List[Dict[str, Any]]) -> str:
    lines = []
    for r in rows:
        if isinstance(r, str):
            lines.append(r)
            continue
        if isinstance(r, dict) and "raw" in r:
            lines.append(str(r["raw"]))
            continue
        if isinstance(r, dict):
            kl = {str(k).lower(): v for k, v in r.items()}
            u = kl.get("url",""); t = kl.get("title",""); d = kl.get("date",""); a = kl.get("abstract",""); c = kl.get("category","")
            if any([u,t,d,a,c]):
                lines.append(f"- {d} | {t} | {u}\n  abstract: {a}\n  category: {c}")
                continue
        lines.append(f"- {json.dumps(r, ensure_ascii=False)}")
    return "\n".join(lines).strip()

# ----------------------------- Optimizer (dual context) -----------------------------

STRUCT_SCHEMA = textwrap.dedent("""
Return ONLY valid JSON with keys:
{
  "answer": string,
  "used_connectors": string[],
  "citations": string[]
}
""").strip()

PROVIDER_SYSTEM = textwrap.dedent("""
You are an AI Research Paper Analysis Assistant that helps developers and researchers by:

1. **Analyzing GitHub Issues**: Extract project requirements, technical specifications, and implementation needs from GitHub issues and comments
2. **Research Paper Discovery**: Find and analyze relevant AI research papers that match project requirements
3. **Recommendation Generation**: Provide actionable recommendations combining project requirements with research insights

**Your Capabilities:**
- Parse GitHub issues to understand project scope and technical requirements
- Match requirements with relevant research papers from the database
- Provide implementation guidance based on research findings
- Suggest relevant papers for literature reviews and gap analysis
- Identify research gaps and collaboration opportunities

**Response Format:** Reply ONLY with the JSON schema specified below.
""").strip()

def build_optimized_prompt_dual_context(
    user_prompt: str,
    issues_text: str,
    papers_text: str,
    provider_cw_tokens: int,
    providers: Dict[str, ProviderConf],
    optimizer: OptimizerConf,
) -> Tuple[str, Dict[str, Any]]:
    dbg = {"provider_context_window": provider_cw_tokens, "optimizer": asdict(optimizer)}

    reserve_reply = int(provider_cw_tokens * 0.25)
    reserve_system = 800
    prompt_budget = max(1000, provider_cw_tokens - reserve_reply - reserve_system)

    context_budget_total = int(prompt_budget * 0.45)
    issues_budget = max(150, context_budget_total // 2)
    papers_budget = max(150, context_budget_total - issues_budget)
    instruction_budget = max(400, prompt_budget - context_budget_total)
    user_budget = max(200, int(instruction_budget * 0.45))

    user_final = user_prompt if est_tokens(user_prompt) <= user_budget else trim_to_tokens(user_prompt, user_budget)

    issues_sum = summarize_to_tokens_dynamic(providers, optimizer, issues_text, issues_budget) if issues_text else ""
    papers_sum = summarize_to_tokens_dynamic(providers, optimizer, papers_text, papers_budget) if papers_text else ""

    try:
        p = providers.get(optimizer.provider)
        if not p: raise RuntimeError(f"Optimizer provider '{optimizer.provider}' not configured")

        sys = "You are a specialized prompt optimizer for AI research paper analysis workflows."
        prompt = f"""Rewrite the user request into a crisp, actionable instruction optimized for research paper analysis and GitHub issue integration.

**Optimization Guidelines:**
- Keep the instruction <= {instruction_budget} tokens (approx)
- Be specific and structured for research paper matching
- Include concrete references (issue #, URLs, table/column names) when present
- Focus on extracting requirements from GitHub issues and matching with research papers
- Emphasize implementation guidance and literature review aspects
- Do NOT include any 'Context:' sections—return only the instruction text

**Research Paper Workflow Focus:**
- Extract technical requirements from GitHub issues
- Match requirements with relevant AI research papers
- Provide implementation recommendations based on research findings
- Suggest papers for literature reviews and gap analysis

User request:
{user_final}

Context A (GitHub Issues, summarized):
{issues_sum}

Context B (Research Papers, summarized):
{papers_sum}
"""
        optimized_instruction = llm_complete(optimizer.provider, p, optimizer.model, prompt, system=sys, temperature=optimizer.temperature).strip() or user_final
        if est_tokens(optimized_instruction) > instruction_budget:
            optimized_instruction = summarize_to_tokens_dynamic(providers, optimizer, optimized_instruction, instruction_budget)
    except Exception as e:
        dbg["optimizer_error"] = str(e)
        optimized_instruction = f"""Analyze the user request by combining GitHub issues/comments with research paper insights to provide comprehensive recommendations.

**Analysis Approach:**
- Extract project requirements and technical specifications from GitHub issues
- Match requirements with relevant AI research papers from the database
- Provide implementation guidance based on research findings
- Suggest relevant papers for literature review and gap analysis

User request:
{user_final}"""

    total_now = est_tokens(optimized_instruction) + est_tokens(issues_sum) + est_tokens(papers_sum)
    if total_now > prompt_budget:
        overflow = total_now - prompt_budget
        cur_i = est_tokens(issues_sum) or 1
        cur_p = est_tokens(papers_sum) or 1
        total_c = cur_i + cur_p
        reduce_i = int(overflow * (cur_i / total_c))
        reduce_p = overflow - reduce_i
        new_i_budget = max(100, cur_i - reduce_i)
        new_p_budget = max(100, cur_p - reduce_p)
        issues_sum = summarize_to_tokens_dynamic(providers, optimizer, issues_sum, new_i_budget)
        papers_sum = summarize_to_tokens_dynamic(providers, optimizer, papers_sum, new_p_budget)

    final_prompt = f"""{optimized_instruction}

**GitHub Issues Context** (Project Requirements & Specifications):
{issues_sum or '(none)'} 

**Research Papers Context** (AI Research Database):
{papers_sum or '(none)'}"""

    if est_tokens(final_prompt) > prompt_budget:
        rem = prompt_budget - est_tokens(optimized_instruction)
        half = max(80, rem // 2)
        issues_sum = summarize_to_tokens_dynamic(providers, optimizer, issues_sum, half)
        papers_sum = summarize_to_tokens_dynamic(providers, optimizer, papers_sum, rem - half)
        final_prompt = f"""{optimized_instruction}

**GitHub Issues Context** (Project Requirements & Specifications):
{issues_sum or '(none)'} 

**Research Papers Context** (AI Research Database):
{papers_sum or '(none)'}"""

    return final_prompt, {
        "budgets": {
            "reserve_reply": reserve_reply,
            "reserve_system": reserve_system,
            "prompt_budget_total": prompt_budget,
            "instruction_budget": instruction_budget,
            "context_budget_total": context_budget_total,
            "issues_budget": issues_budget,
            "papers_budget": papers_budget,
            "user_budget": user_budget,
        },
        "final_tokens_est": est_tokens(final_prompt),
    }

# ----------------------------- Views -----------------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.get("/api/settings")
def api_get_settings():
    s = load_settings()
    return jsonify({
        "providers": {k: asdict(v) for k, v in s.providers.items()},
        "mcp": s.mcp,
        "optimizer": asdict(s.optimizer),
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
    if "optimizer" in data:
        cur.optimizer = OptimizerConf(**{**asdict(cur.optimizer), **data["optimizer"]})
    save_settings(cur)
    return jsonify({"ok": True})

@app.post("/api/optimize")
def api_optimize():
    s = load_settings()
    user_prompt = (request.json.get("user_prompt") or "").strip()
    provider_key = (request.json.get("provider") or "anthropic").strip()

    gh_conf = MCPGitHubConf(**s.mcp["github"])
    pg_conf = MCPPostgresConf(**s.mcp["postgres"])

    dbg = {"github": None, "postgres": None, "optimizer": None}

    # Gather contexts (with error handling)
    issues_text = ""
    try:
        gh = asyncio.run(fetch_github_issues_and_comments(gh_conf, limit_issues=3, limit_comments=5))
        dbg["github"] = gh.get("debug")
        issues_text = render_issues_raw_text(gh.get("issues", []))
    except Exception as e:
        dbg["github"] = {"error": f"MCP GitHub connection failed: {str(e)}"}

    papers_text = ""
    try:
        pg = asyncio.run(fetch_research_papers(pg_conf, limit_rows=8))
        dbg["postgres"] = pg.get("debug")
        papers_text = render_papers_raw_text(pg.get("rows", []))
    except Exception as e:
        dbg["postgres"] = {"error": f"MCP Postgres connection failed: {str(e)}"}

    provider_conf = s.providers.get(provider_key) or s.providers["anthropic"]
    cw = provider_conf.context_window or 128000

    final_prompt, opt_dbg = build_optimized_prompt_dual_context(
        user_prompt=user_prompt,
        issues_text=issues_text,
        papers_text=papers_text,
        provider_cw_tokens=cw,
        providers=s.providers,
        optimizer=s.optimizer,
    )
    dbg["optimizer"] = opt_dbg

    return jsonify({"optimized_prompt": final_prompt, "debug": dbg})

@app.post("/api/chat")
def api_chat():
    s = load_settings()
    provider = request.json.get("provider", "anthropic")
    model = request.json.get("model") or None
    user_prompt = (request.json.get("user_prompt") or "").strip()

    # Re-fetch MCP contexts for fresh grounding (with error handling)
    issues_text = ""
    papers_text = ""
    gh_debug = {"error": "MCP GitHub not available"}
    pg_debug = {"error": "MCP Postgres not available"}
    
    try:
        gh = asyncio.run(fetch_github_issues_and_comments(MCPGitHubConf(**s.mcp["github"]), 3, 5))
        issues_text = render_issues_raw_text(gh.get("issues", []))
        gh_debug = gh.get("debug", {})
    except Exception as e:
        gh_debug = {"error": f"MCP GitHub connection failed: {str(e)}"}
    
    try:
        pg = asyncio.run(fetch_research_papers(MCPPostgresConf(**s.mcp["postgres"]), 8))
        papers_text = render_papers_raw_text(pg.get("rows", []))
        pg_debug = pg.get("debug", {})
    except Exception as e:
        pg_debug = {"error": f"MCP Postgres connection failed: {str(e)}"}

    pconf = s.providers.get(provider) or s.providers["anthropic"]
    cw = pconf.context_window or 128000
    final_prompt, opt_dbg = build_optimized_prompt_dual_context(
        user_prompt=user_prompt,
        issues_text=issues_text,
        papers_text=papers_text,
        provider_cw_tokens=cw,
        providers=s.providers,
        optimizer=s.optimizer,
    )

    sys_prompt = f"{PROVIDER_SYSTEM}\n\nSchema:\n{STRUCT_SCHEMA}"
    raw = ""
    provider_debug = {
        "name": pconf.name or provider,
        "model": model or pconf.default_model,
        "endpoint": pconf.base_url,
        "request": {
            "system_preview": _snip_text(sys_prompt, 800),
            "prompt_preview": _snip_text(final_prompt, 800),
            "temperature": pconf.temperature,
        }
    }

    try:
        if provider == "openai":
            raw = call_openai(pconf.base_url, pconf.api_key, provider_debug["model"], sys_prompt, final_prompt, pconf.temperature)
        elif provider == "anthropic":
            try:
                raw = call_anthropic(pconf.base_url, pconf.api_key, provider_debug["model"], sys_prompt, final_prompt, pconf.temperature)
            except requests.HTTPError as e:
                raw = json.dumps({"answer": f"Provider error: {e} @ {_anth_endpoint(pconf.base_url, 'messages')}", "used_connectors": [], "citations": []})
        elif provider == "ollama":
            raw = call_ollama(pconf.base_url, provider_debug["model"], f"{sys_prompt}\n\n{final_prompt}\n\nRespond with JSON only.", pconf.temperature)
        elif provider == "google":
            raw = call_google(pconf.base_url, pconf.api_key, provider_debug["model"], sys_prompt, final_prompt, pconf.temperature)
        else:
            raise RuntimeError(f"Unknown provider: {provider}")
    except requests.HTTPError as e:
        # Handle HTTP errors specifically
        error_msg = f"HTTP Error: {e}"
        if hasattr(e, 'response') and e.response is not None:
            error_msg = f"HTTP Error {e.response.status_code}: {e}"
            try:
                error_body = e.response.text[:500]
                error_msg += f" - Response: {error_body}"
            except:
                pass
        raw = json.dumps({"answer": error_msg, "used_connectors": [], "citations": []})
        provider_debug["error"] = str(e)
    except Exception as e:
        # Handle other exceptions
        raw = json.dumps({"answer": f"Provider error: {e}", "used_connectors": [], "citations": []})
        provider_debug["error"] = str(e)

    provider_debug["response"] = {
        "raw_preview": _snip_text(raw, 1400)
    }

    # Robust parse (use your existing parse if you already added it)
    try:
        structured = json.loads(raw)
    except Exception:
        structured = {"answer": raw, "used_connectors": [], "citations": []}

    provider_debug["parsed"] = {
        "structured_preview": _snip(structured, 1400)
    }

    debug = {
        "mcp": {
            "github": gh_debug,
            "postgres": pg_debug,
        },
        "optimizer": opt_dbg,
        "provider": provider_debug,
        "final_prompt_tokens_est": est_tokens(final_prompt),
    }

    return jsonify({
        "text": raw,
        "structured": json.dumps(structured, ensure_ascii=False, indent=2),
        "debug": debug
    })



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5050")), debug=True)
