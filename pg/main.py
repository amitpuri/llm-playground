import os, json, asyncio
from typing import Any
from dotenv import load_dotenv
from fastmcp import Client

# ------ helpers: parse TextContent / list-of-TextContent ------
def _is_textcontent(x: Any) -> bool:
    return hasattr(x, "text") and isinstance(getattr(x, "text"), str)

def to_json(payload: Any) -> Any:
    data = getattr(payload, "content", payload)
    if isinstance(data, dict) and "content" in data:
        data = data["content"]

    # list[TextContent] FIRST
    if isinstance(data, list) and data and _is_textcontent(data[0]):
        try:
            return json.loads(data[0].text)
        except Exception:
            try:
                joined = "".join(getattr(tc, "text", "") for tc in data if _is_textcontent(tc))
                return json.loads(joined)
            except Exception:
                return [getattr(tc, "text", "") for tc in data if _is_textcontent(tc)]

    # single TextContent
    if _is_textcontent(data):
        try:
            return json.loads(data.text)
        except Exception:
            return data.text

    # already JSON-like (dict/list) or None/str
    return data

# --- pretty + coercer for stringified payloads / non-JSON types ---
import json as _json, datetime, decimal, uuid, ast
from zoneinfo import ZoneInfo

def _json_default(o):
    if isinstance(o, (datetime.datetime, datetime.date, datetime.time)):
        return o.isoformat()
    if isinstance(o, ZoneInfo):
        return o.key
    if isinstance(o, decimal.Decimal):
        return float(o)
    if isinstance(o, uuid.UUID):
        return str(o)
    return str(o)

def coerce_jsonish(x):
    """
    Convert server replies like ["[{'k': 1}]"] or ["{\"k\":1}"] into real JSON.
    - Tries json.loads first
    - Falls back to ast.literal_eval for Python-ish repr
    """
    if isinstance(x, list) and len(x) == 1 and isinstance(x[0], str):
        s = x[0].strip()
        if s and s[0] in "[{" and s[-1] in "]}":
            try:
                return _json.loads(s)
            except Exception:
                try:
                    return ast.literal_eval(s)
                except Exception:
                    return x
    return x

def pretty(x, n: int = 800) -> str:
    try:
        return _json.dumps(x, ensure_ascii=False, indent=2, default=_json_default)[:n]
    except Exception:
        try:
            return str(x)[:n]
        except Exception:
            return repr(x)[:n]

# --- top-1 row helper (JSON-safe via row_to_json) ---
async def fetch_top1_row(client, schema_name: str, table_name: str):
    fq = f'"{schema_name}"."{table_name}"'
    sql = f"""
    SELECT row_to_json(t) AS row
    FROM (
        SELECT *
        FROM {fq}
        LIMIT 1
    ) t;
    """
    res = await client.call_tool("execute_sql", {"sql": sql})
    data = coerce_jsonish(to_json(res))

    # Normalize shapes
    if isinstance(data, dict):
        rows = data.get("rows") or data.get("items") or data.get("results") or []
        if rows and isinstance(rows, list):
            first = rows[0]
            if isinstance(first, dict) and isinstance(first.get("row"), dict):
                return first["row"]
            if isinstance(first, dict):
                return first
        return data
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict) and isinstance(first.get("row"), dict):
            return first["row"]
        if isinstance(first, dict):
            return first
    return data

# ------ main demo ------
async def main():
    load_dotenv()
    url = os.getenv("POSTGRES_MCP_URL", "http://localhost:8000/sse")

    client = Client(url)  # SSE URL; no auth for local
    async with client:
        # 1) tools
        tools = await client.list_tools()
        tool_names = sorted([getattr(t, "name", None) or t.get("name") for t in tools])
        print("Tools:", tool_names)

        # 2) list schemas
        res = await client.call_tool("list_schemas", {})
        schemas = coerce_jsonish(to_json(res))
        print("\nSchemas:", pretty(schemas))

        # 3) list objects in research_papers (you can switch to 'public' if needed)
        res = await client.call_tool("list_objects", {"schema_name": "research_papers"})
        objs = to_json(res)
        print("\nresearch_papers objects:", pretty(coerce_jsonish(objs), 2000))

        # choose a table and show details (NOTE: param must be object_name)
        tables = [o.get("name") for o in (coerce_jsonish(objs) or [])
                  if isinstance(o, dict) and str(o.get("type") or o.get("object_type") or "").lower() == "table"]
        if tables:
            table = tables[0]
            res = await client.call_tool(
                "get_object_details",
                {"schema_name": "research_papers", "object_name": table}
            )
            details = coerce_jsonish(to_json(res))
            print(f"\nDetails for research_papers.{table}:", pretty(details, 2000))

        # 4) safe sample query
        res = await client.call_tool("execute_sql", {"sql": "SELECT NOW() AS server_time"})
        print("\nQuery result:", pretty(coerce_jsonish(to_json(res))))

        # 5) EXPLAIN plan
        res = await client.call_tool("explain_query", {"sql": "SELECT 1"})
        plan = to_json(res)
        print("\nEXPLAIN plan:", pretty(coerce_jsonish(plan)))

        # 6) DB health
        res = await client.call_tool("analyze_db_health", {})
        health = to_json(res)
        print("\nDB Health (summary):", pretty(coerce_jsonish(health), 2000))

        # 7) TOP 1 ROW FROM research_papers.ai_research_papers
        row = await fetch_top1_row(client, "research_papers", "ai_research_papers")
        print("\nTop 1 row from research_papers.ai_research_papers:")
        print(pretty(row, 2000))

        # 8) explicit object details for that table (again, object_name)
        res = await client.call_tool(
            "get_object_details",
            {"schema_name": "research_papers", "object_name": "ai_research_papers"}
        )
        print("\nTable details:", pretty(coerce_jsonish(to_json(res)), 2000))

if __name__ == "__main__":
    asyncio.run(main())
