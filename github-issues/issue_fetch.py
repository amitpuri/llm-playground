import os, sys, json, asyncio
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.auth import BearerAuth

# === Utilities ===

def env(key: str, default: Optional[str] = None) -> str:
    v = os.getenv(key, default)
    if v is None:
        raise RuntimeError(f"Missing env var: {key}")
    return v

def is_textcontent(x: Any) -> bool:
    # FastMCP TextContent usually has attr .text
    return hasattr(x, "text") and isinstance(getattr(x, "text"), str)

def unwrap_content(payload: Any) -> Any:
    """Return payload.content if present; else payload."""
    return getattr(payload, "content", payload)

def to_json(payload: Any) -> Any:
    data = getattr(payload, "content", payload)
    if isinstance(data, dict) and "content" in data:
        data = data["content"]

    # handle list-of-TextContent first
    if isinstance(data, list) and data and hasattr(data[0], "text") and isinstance(data[0].text, str):
        try:
            return json.loads(data[0].text)
        except Exception:
            try:
                joined = "".join(getattr(tc, "text", "") for tc in data)
                return json.loads(joined)
            except Exception:
                return [getattr(tc, "text", "") for tc in data]

    # single TextContent
    if hasattr(data, "text") and isinstance(data.text, str):
        try:
            return json.loads(data.text)
        except Exception:
            return data.text

    if isinstance(data, (dict, list)):
        return data
    return data

def ensure_dict(obj: Any) -> Optional[Dict[str, Any]]:
    """Return a dict if obj is a dict, or a one-element list containing a dict; else None."""
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                return item
    return None

def pretty(x: Any) -> str:
    try:
        return json.dumps(x, indent=2, ensure_ascii=False)
    except Exception:
        return repr(x)

# === Core ===

async def mcp_get_issue(client: Client, owner: str, repo: str, issue_number: int, verbose: bool = True) -> Optional[Dict[str, Any]]:
    """Call get_issue and robustly parse, returning a dict or None."""
    try:
        res = await client.call_tool("get_issue", {"owner": owner, "repo": repo, "issue_number": issue_number})
    except Exception as e:
        if verbose:
            print(f"[get_issue] ERROR for #{issue_number}: {e!r}", file=sys.stderr)
        return None

    raw = unwrap_content(res)
    if verbose:
        print(f"[get_issue] raw type={type(raw).__name__}")

    parsed = to_json(res)
    if verbose:
        short = pretty(parsed)
        print(f"[get_issue] parsed (first 1KB): {short[:1024]}")

    if parsed is None:
        # JSON 'null' or truly empty payload
        if verbose:
            print("[get_issue] parsed is None (JSON null or empty).", file=sys.stderr)
        return None

    doc = ensure_dict(parsed)
    if not doc:
        if verbose:
            print("[get_issue] could not normalize to dict.", file=sys.stderr)
        return None
    return doc

async def mcp_get_issue_comments(client: Client, owner: str, repo: str, issue_number: int, verbose: bool = False) -> List[Dict[str, Any]]:
    """Call get_issue_comments and parse to list of dicts."""
    try:
        res = await client.call_tool("get_issue_comments", {
            "owner": owner, "repo": repo, "issue_number": issue_number,
            "page": 1, "per_page": 100
        })
    except Exception as e:
        if verbose:
            print(f"[get_issue_comments] ERROR for #{issue_number}: {e!r}", file=sys.stderr)
        return []

    parsed = to_json(res)
    if isinstance(parsed, dict):
        for key in ("comments", "items", "results", "nodes"):
            arr = parsed.get(key)
            if isinstance(arr, list):
                return [c for c in arr if isinstance(c, dict)]
        # GraphQL-style edges
        edges = parsed.get("edges")
        if isinstance(edges, list):
            out = []
            for e in edges:
                if isinstance(e, dict) and isinstance(e.get("node"), dict):
                    out.append(e["node"])
            return out
        return []
    elif isinstance(parsed, list):
        return [c for c in parsed if isinstance(c, dict)]
    else:
        return []

async def fetch_one_or_range(owner: str, repo: str, issue_number: Optional[int], probe_from: int, probe_to: int) -> List[Dict[str, Any]]:
    """
    If issue_number is provided, fetch that one; else probe a range (inclusive).
    Returns list of OPEN issue dicts (with comments attached).
    """
    load_dotenv()
    token = env("GITHUB_TOKEN")
    mcp   = os.getenv("MCP_SERVER_URL", "https://api.githubcopilot.com/mcp/")

    client = Client(mcp, auth=BearerAuth(token))
    out: List[Dict[str, Any]] = []
    async with client:
        # print current identity (useful sanity check)
        try:
            me = await client.call_tool("get_me", {})
            me_parsed = to_json(me)
            print("[get_me]", pretty(me_parsed)[:600])
        except Exception as e:
            print(f"[get_me] error: {e!r}", file=sys.stderr)

        targets = [issue_number] if issue_number is not None else list(range(probe_from, probe_to + 1))
        for n in targets:
            if n is None:
                continue
            doc = await mcp_get_issue(client, owner, repo, n, verbose=True)
            if not doc:
                continue
            state = str(doc.get("state", "")).lower()
            if state != "open":
                # if you want all states, drop this check
                continue

            comments = await mcp_get_issue_comments(client, owner, repo, n, verbose=False)
            doc["comments_data"] = comments
            out.append(doc)

    return out

# === CLI ===

async def main():
    load_dotenv()
    repo_slug = env("GITHUB_REPO")  # format: owner/repo
    if "/" not in repo_slug:
        raise RuntimeError("GITHUB_REPO must be in the form owner/repo")
    owner, repo = repo_slug.split("/", 1)

    # Choose either a single ISSUE_NUMBER or a probe range
    issue_number = os.getenv("ISSUE_NUMBER")
    issue_number = int(issue_number) if issue_number and issue_number.isdigit() else None

    # Optional probe range via envs; defaults probe 1..30 if ISSUE_NUMBER not set
    PROBE_FROM = int(os.getenv("PROBE_FROM", "1"))
    PROBE_TO   = int(os.getenv("PROBE_TO", "30"))

    issues = await fetch_one_or_range(owner, repo, issue_number, PROBE_FROM, PROBE_TO)

    print(f"\nFound {len(issues)} OPEN issue(s).")
    out_path = f"open_issues_direct_{owner}_{repo}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(issues, f, ensure_ascii=False, indent=2)
    print(f"Saved to {out_path}")

    # brief summary
    for it in issues:
        print(f"- #{it.get('number')} {it.get('title')} — {len(it.get('comments_data', []))} comment(s)")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
