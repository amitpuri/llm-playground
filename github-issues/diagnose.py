import os, asyncio, json, sys
from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.auth import BearerAuth

def j(x): 
    try: return json.dumps(x, indent=2, ensure_ascii=False)
    except: return str(x)

async def call(client, tool, args):
    try:
        res = await client.call_tool(tool, args)
        return {"ok": True, "content": getattr(res, "content", res)}
    except Exception as e:
        # capture as much detail as possible
        return {"ok": False, "error": repr(e)}

async def main():
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    mcp_url = os.getenv("MCP_SERVER_URL", "https://api.githubcopilot.com/mcp/")
    repo = os.getenv("GITHUB_REPO", "")
    if not token or not repo or "/" not in repo:
        print("Missing env. Need GITHUB_TOKEN and GITHUB_REPO=owner/repo", file=sys.stderr)
        sys.exit(2)
    owner, name = repo.split("/", 1)

    client = Client(mcp_url, auth=BearerAuth(token))
    async with client:
        # 1) Who am I?
        me = await call(client, "get_me", {})
        print("\n[get_me]:", j(me))

        # 2) Can the server find the repository by search?
        q = f"repo:{owner}/{name}"
        sr = await call(client, "search_repositories", {"query": q, "page": 1, "per_page": 5})
        print("\n[search_repositories]:", j(sr))

        # 3) Can it read a file from the repo (proves repo visibility)?
        gf = await call(client, "get_file_contents", {"owner": owner, "repo": name, "path": "README.md"})
        print("\n[get_file_contents README.md]:", j(gf))

        # 4) Can we fetch the specific issue #3 (or whichever)?
        gi = await call(client, "get_issue", {"owner": owner, "repo": name, "issue_number": 3})
        print("\n[get_issue #3]:", j(gi))

        # 5) If the issue is visible, try comments too
        if gi.get("ok") and isinstance(gi.get("content"), dict):
            gc = await call(client, "get_issue_comments", {"owner": owner, "repo": name, "issue_number": 3})
            print("\n[get_issue_comments #3]:", j(gc))

if __name__ == "__main__":
    asyncio.run(main())
