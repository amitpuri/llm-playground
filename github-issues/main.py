import os, sys, json, asyncio, re
from typing import Any, Dict, List, Optional, Tuple, Iterable, Union
from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.auth import BearerAuth

# ----------------- utils -----------------
def require_env(key: str) -> str:
    v = os.getenv(key)
    if not v:
        raise RuntimeError(f"Missing env var: {key}")
    return v

def _get_name(tool: Any) -> Optional[str]:
    if hasattr(tool, "name"): return getattr(tool, "name")
    if isinstance(tool, dict): return tool.get("name")
    return None

def tool_names(tools: Iterable[Any]) -> List[str]:
    return [n for n in (_get_name(t) for t in tools) if n]

def normalize_state(v: Any) -> str:
    return str(v).strip().lower()

# ---------- TextContent-aware JSON unpackers ----------
def _maybe_textcontent(obj: Any) -> bool:
    # FastMCP returns a list of TextContent (pydantic model) with `.text`
    return hasattr(obj, "text") and isinstance(getattr(obj, "text"), str)

def to_json_value(payload: Any) -> Any:
    """
    Convert MCP responses into Python JSON structures.
    Handles, in this order:
      - list[TextContent] with .text JSON  ✅ (FIRST)
      - TextContent itself
      - {"content": ...} wrappers
      - raw dict/list
    """
    # unwrap `.content` if present
    data = getattr(payload, "content", payload)
    if isinstance(data, dict) and "content" in data:
        data = data["content"]

    # 1) If it's a list of TextContent (most common for this server) → decode JSON
    if isinstance(data, list) and data and _maybe_textcontent(data[0]):
        try:
            return json.loads(data[0].text)           # first item usually has the full JSON
        except Exception:
            try:
                combined = "".join(tc.text for tc in data if _maybe_textcontent(tc))
                return json.loads(combined)
            except Exception:
                return [tc.text for tc in data if _maybe_textcontent(tc)]

    # 2) If it's a single TextContent
    if _maybe_textcontent(data):
        try:
            return json.loads(data.text)
        except Exception:
            return data.text  # as plain string

    # 3) Already dict/list? return as-is
    if isinstance(data, (dict, list)):
        return data

    # 4) Anything else (None, simple str, etc.)
    return data

def extract_issue_list(doc: Any) -> List[Dict[str, Any]]:
    """
    From any JSON doc, return a list of issue dicts.
    Supports: items/issues/results/nodes/edges/node/data nesting.
    """
    if hasattr(doc, "dict"):
        doc = doc.dict()

    if isinstance(doc, dict):
        for key in ("items", "issues", "results", "nodes"):
            arr = doc.get(key)
            if isinstance(arr, list):
                return [x.get("node", x) for x in arr if isinstance(x, (dict,))]
        # GraphQL-ish edges
        edges = doc.get("edges")
        if isinstance(edges, list):
            out = []
            for e in edges:
                if isinstance(e, dict) and isinstance(e.get("node"), dict):
                    out.append(e["node"])
            return out
        # sometimes nested one level deeper
        data = doc.get("data")
        if isinstance(data, dict):
            return extract_issue_list(data)
        # single issue object case
        if "id" in doc and "number" in doc:
            return [doc]
        return []
    if isinstance(doc, list):
        return [x for x in doc if isinstance(x, dict)]
    return []

def extract_comment_list(doc: Any) -> List[Dict[str, Any]]:
    if hasattr(doc, "dict"):
        doc = doc.dict()
    if isinstance(doc, dict):
        for key in ("items", "comments", "results", "nodes"):
            arr = doc.get(key)
            if isinstance(arr, list):
                return [x.get("node", x) for x in arr if isinstance(x, dict)]
        edges = doc.get("edges")
        if isinstance(edges, list):
            out = []
            for e in edges:
                if isinstance(e, dict) and isinstance(e.get("node"), dict):
                    out.append(e["node"])
            return out
        data = doc.get("data")
        if isinstance(data, dict):
            return extract_comment_list(data)
        return []
    if isinstance(doc, list):
        return [x for x in doc if isinstance(x, dict)]
    return []

def derive_issue_number(issue: Dict[str, Any]) -> Optional[int]:
    n = issue.get("number")
    if isinstance(n, int):
        return n
    for k in ("url", "html_url"):
        u = issue.get(k)
        if isinstance(u, str) and "/issues/" in u:
            m = re.search(r"/issues/(\d+)", u)
            if m:
                return int(m.group(1))
    return None

# ----------------- discovery -----------------
async def pick_tools(client: Client) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    tools_list = await client.list_tools()
    names = set(tool_names(tools_list))
    print("Available tools on server:")
    for n in sorted(names):
        print(f"  - {n}")
    issues_search = "search_issues" if "search_issues" in names else None
    issues_list   = "list_issues"   if "list_issues"   in names else None
    comments_tool = "get_issue_comments" if "get_issue_comments" in names else None
    if not (issues_search or issues_list):
        raise RuntimeError("No issues tool found (need search_issues or list_issues).")
    return issues_search, issues_list, comments_tool

# ----------------- fetchers -----------------
async def search_open_issues(client: Client, search_tool: str, owner: str, repo: str) -> List[Dict[str, Any]]:
    """
    Use search_issues (query=...) and parse TextContent JSON.
    """
    collected: List[Dict[str, Any]] = []
    query_variants = [
        f"repo:{owner}/{repo} is:issue is:open",
        f"repo:{owner}/{repo} type:issue state:open",
        f"repo:{owner}/{repo} is:open is:issue",
        f"repo:{owner}/{repo} state:open",
    ]
    for q in query_variants:
        page, per_page = 1, 100
        while True:
            raw = await client.call_tool(search_tool, {"query": q, "page": page, "per_page": per_page})
            doc = to_json_value(raw)
            batch = extract_issue_list(doc)
            if not batch:
                break
            # ensure open
            batch = [x for x in batch if normalize_state(x.get("state")) == "open"]
            collected.extend(batch)
            if len(batch) < per_page:
                break
            page += 1
        if collected:
            return collected

    # broad search then local filter
    for q in [f"repo:{owner}/{repo} is:issue", f"repo:{owner}/{repo}"]:
        raw = await client.call_tool(search_tool, {"query": q, "page": 1, "per_page": 100})
        doc = to_json_value(raw)
        batch = [x for x in extract_issue_list(doc) if normalize_state(x.get("state")) == "open"]
        if batch:
            return batch
    return []

async def list_open_issues(client: Client, issues_tool: str, owner: str, repo: str) -> List[Dict[str, Any]]:
    """
    Use list_issues with common arg shapes; parse TextContent JSON.
    """
    collected: List[Dict[str, Any]] = []
    page, per_page = 1, 100
    variants = [
        {"owner": owner, "repo": repo, "state": "open"},
        {"owner": owner, "repo": repo, "state": "OPEN"},
        {"owner": owner, "repo": repo, "states": ["OPEN"]},
        {"owner": owner, "repo": repo, "filter": "all", "state": "open"},
        {"owner": owner, "repo": repo},  # local-filter if needed
    ]
    chosen, supports_pagination = None, True
    while True:
        last_err = None
        for base in ([chosen] if chosen else variants):
            payload = dict(base)
            if supports_pagination:
                payload.update({"page": page, "per_page": per_page})
            try:
                raw = await client.call_tool(issues_tool, payload)
                doc = to_json_value(raw)
                batch = extract_issue_list(doc)
                if chosen is None:
                    chosen = base
            except Exception as e:
                last_err = e
                continue
            break
        else:
            if supports_pagination:
                supports_pagination, page = False, 1
                continue
            raise RuntimeError("list_issues failed with all payload variants") from last_err

        if not batch:
            if page == 1 and supports_pagination:
                supports_pagination = False
                continue

        collected.extend(batch)
        if not supports_pagination or len(batch) < per_page:
            break
        page += 1

    # local open filter
    return [x for x in collected if normalize_state(x.get("state")) == "open"]

async def list_issue_comments(client: Client, comments_tool: str, owner: str, repo: str, issue_number: int) -> List[Dict[str, Any]]:
    all_comments: List[Dict[str, Any]] = []
    page, per_page = 1, 100
    while True:
        try:
            raw = await client.call_tool(
                comments_tool,
                {"owner": owner, "repo": repo, "issue_number": issue_number, "page": page, "per_page": per_page},
            )
        except Exception:
            raw = await client.call_tool(comments_tool, {"owner": owner, "repo": repo, "issue_number": issue_number})
            doc = to_json_value(raw)
            return extract_comment_list(doc)
        doc = to_json_value(raw)
        batch = extract_comment_list(doc)
        if not batch:
            break
        all_comments.extend(batch)
        if len(batch) < per_page:
            break
        page += 1
    return all_comments

async def direct_get_fallback(client: Client, owner: str, repo: str, ids: List[int]) -> List[Dict[str, Any]]:
    found = []
    for n in ids:
        try:
            raw = await client.call_tool("get_issue", {"owner": owner, "repo": repo, "issue_number": n})
            doc = to_json_value(raw)
            # get_issue may return a single dict or a list with one dict
            if isinstance(doc, list):
                for item in doc:
                    if isinstance(item, dict) and normalize_state(item.get("state")) == "open":
                        found.append(item)
            elif isinstance(doc, dict):
                if normalize_state(doc.get("state")) == "open":
                    found.append(doc)
        except Exception as e:
            # uncomment to debug specific failures:
            # print(f"[debug] get_issue #{n} failed: {e!r}", file=sys.stderr)
            pass
    return found

# ----------------- main -----------------
async def main():
    load_dotenv()
    token = require_env("GITHUB_TOKEN")
    mcp_url = os.getenv("MCP_SERVER_URL", "https://api.githubcopilot.com/mcp/")
    repo_slug = require_env("GITHUB_REPO")
    if "/" not in repo_slug:
        raise RuntimeError("GITHUB_REPO must be owner/repo")
    owner, repo = repo_slug.split("/", 1)

    client = Client(mcp_url, auth=BearerAuth(token))
    async with client:
        search_tool, list_tool, comments_tool = await pick_tools(client)

        issues: List[Dict[str, Any]] = []
        if search_tool:
            issues = await search_open_issues(client, search_tool, owner, repo)
        if not issues and list_tool:
            issues = await list_open_issues(client, list_tool, owner, repo)
        if not issues:
            # Your diagnose showed issue #3 exists; probe that and a few nearby IDs
            print("Both search_issues and list_issues empty; probing direct get_issue…", file=sys.stderr)
            probe_ids = [3] + list(range(1, 30))
            issues = await direct_get_fallback(client, owner, repo, probe_ids)

        print(f"\nFound {len(issues)} OPEN issues in {owner}/{repo}")

        if comments_tool and issues:
            for i, issue in enumerate(issues, start=1):
                number = issue.get("number") or derive_issue_number(issue)
                if isinstance(number, int):
                    comments = await list_issue_comments(client, comments_tool, owner, repo, number)
                    issue["comments_data"] = comments
                else:
                    issue["comments_data"] = []
                if i % 25 == 0:
                    print(f"  processed {i}/{len(issues)} issues…", file=sys.stderr)
        elif not comments_tool:
            print("Warning: no get_issue_comments tool; returning issues without comments.", file=sys.stderr)

        out_path = f"open_issues_with_comments_{owner}_{repo}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(issues, f, ensure_ascii=False, indent=2)

        for issue in issues[:10]:
            title = issue.get("title")
            number = issue.get("number") or derive_issue_number(issue)
            state = issue.get("state")
            comment_count = len(issue.get("comments_data", []))
            print(f"#{number} [{state}] {title} — {comment_count} comment(s)")
        if len(issues) > 10:
            print(f"...and {len(issues) - 10} more issues.")
        print(f"\nSaved full data to {out_path}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
