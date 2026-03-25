"""X-Ray configuration viewing API endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/memory")
async def get_memory(request: Request):
    """Get current memory content."""
    refs = request.app.state.config_refs
    memory_store = refs.get("memory_store")
    if memory_store is None:
        return {"content": "", "available": False}
    try:
        # BaseMemoryStore.read_long_term() is synchronous
        content = memory_store.read_long_term()
        return {"content": content, "available": True}
    except Exception as e:
        return {"content": "", "available": False, "error": str(e)}


@router.get("/soul")
async def get_soul(request: Request):
    """Get Soul configuration."""
    refs = request.app.state.config_refs
    workspace = refs.get("workspace", ".")

    # Check .nanobot/SOUL.md first, then workspace root
    soul_path = Path(workspace) / ".nanobot" / "SOUL.md"
    if not soul_path.exists():
        soul_path = Path(workspace) / "SOUL.md"

    if soul_path.exists():
        return {
            "content": soul_path.read_text(encoding="utf-8"),
            "path": str(soul_path),
        }
    return {"content": "", "path": "", "available": False}


@router.get("/skills")
async def get_skills(request: Request):
    """Get skills list and content."""
    refs = request.app.state.config_refs
    skills_loader = refs.get("skills_loader")
    if skills_loader is None:
        return {"skills": [], "available": False}
    try:
        # list_skills returns list of dicts with name, path, source
        skill_infos = skills_loader.list_skills()
        skills = []
        for info in skill_infos:
            name = info["name"]
            content = skills_loader.load_skill(name)
            skills.append({
                "name": name,
                "content": content or "",
                "path": info.get("path", ""),
                "source": info.get("source", ""),
            })
        return {"skills": skills, "count": len(skills)}
    except Exception as e:
        return {"skills": [], "error": str(e)}


@router.get("/mcp")
async def get_mcp(request: Request):
    """Get MCP servers and tool list."""
    refs = request.app.state.config_refs
    tool_registry = refs.get("tool_registry")
    bot_config = refs.get("bot_config")

    mcp_tools = []
    if tool_registry:
        all_tools = tool_registry.get_definitions()
        mcp_tools = [
            t
            for t in all_tools
            if t.get("function", {}).get("name", "").startswith("mcp_")
        ]

    mcp_servers = {}
    if bot_config and hasattr(bot_config, "tools") and hasattr(bot_config.tools, "mcp_servers"):
        # Serialize MCP server config (excluding sensitive info)
        servers_config = bot_config.tools.mcp_servers or {}
        for name in servers_config:
            # Count tools for this server
            tool_count = len([
                t
                for t in mcp_tools
                if t.get("function", {}).get("name", "").startswith(f"mcp_{name}_")
            ])
            mcp_servers[name] = {"name": name, "tool_count": tool_count}

    return {"servers": mcp_servers, "tools": mcp_tools, "tool_count": len(mcp_tools)}


@router.get("/tools")
async def get_tools(request: Request):
    """Get all registered tool definitions."""
    refs = request.app.state.config_refs
    tool_registry = refs.get("tool_registry")
    if tool_registry is None:
        return {"tools": [], "available": False}
    tools = tool_registry.get_definitions()
    return {"tools": tools, "count": len(tools)}
