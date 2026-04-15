"""Stdio MCP transport for the catalog server."""

from __future__ import annotations

import asyncio
import json
import os
import sys

from catalog.src.db import init_db
from catalog.src.mcp_tools import (
    catalog_recommend,
    catalog_search,
    catalog_similar,
    catalog_stats,
)

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool

    HAS_MCP = True
except ImportError:
    HAS_MCP = False


def _get_db_path() -> str:
    """Resolve database path from env or default."""
    return os.environ.get(
        "CATALOG_DB",
        os.path.join(os.path.dirname(__file__), "..", "data", "catalog.db"),
    )


def _build_server() -> "Server":
    """Build and configure the MCP server with catalog tools."""
    if not HAS_MCP:
        raise RuntimeError(
            "mcp package is not installed. Install with: pip install mcp>=1.0.0"
        )

    server = Server("catalog")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="catalog_search",
                description="Search the component catalog with filters.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Text to search in name, description, tags.",
                        },
                        "type": {
                            "type": "string",
                            "description": "Component type filter.",
                            "enum": ["skill", "agent", "hook", "plugin", "command"],
                        },
                        "project_type": {
                            "type": "string",
                            "description": "Project type filter (e.g. devops, app-deploy).",
                        },
                        "persona": {
                            "type": "string",
                            "description": "Target persona filter (e.g. platform-engineer, cloud-sre).",
                        },
                        "min_stars": {
                            "type": "integer",
                            "description": "Minimum repo stars.",
                            "default": 0,
                        },
                        "sort_by": {
                            "type": "string",
                            "description": "Sort order.",
                            "enum": ["relevance", "stars", "recent"],
                            "default": "relevance",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max results to return.",
                            "default": 20,
                        },
                    },
                    "additionalProperties": False,
                },
            ),
            Tool(
                name="catalog_recommend",
                description="Get recommended components for a project type and/or persona, with similar items collapsed.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_type": {
                            "type": "string",
                            "description": "Project type to recommend for.",
                        },
                        "persona": {
                            "type": "string",
                            "description": "Target persona to recommend for.",
                        },
                    },
                    "additionalProperties": False,
                },
            ),
            Tool(
                name="catalog_similar",
                description="Find components similar to a given component.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "component_id": {
                            "type": "integer",
                            "description": "ID of the component to find similarities for.",
                        },
                    },
                    "required": ["component_id"],
                    "additionalProperties": False,
                },
            ),
            Tool(
                name="catalog_stats",
                description="Get aggregate statistics about the catalog.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        db_path = _get_db_path()
        conn = init_db(db_path)
        try:
            if name == "catalog_search":
                result = catalog_search(
                    conn,
                    query=arguments.get("query", ""),
                    type=arguments.get("type", ""),
                    project_type=arguments.get("project_type", ""),
                    persona=arguments.get("persona", ""),
                    min_stars=arguments.get("min_stars", 0),
                    sort_by=arguments.get("sort_by", "relevance"),
                    limit=arguments.get("limit", 20),
                )
            elif name == "catalog_recommend":
                result = catalog_recommend(
                    conn,
                    project_type=arguments.get("project_type", ""),
                    persona=arguments.get("persona", ""),
                )
            elif name == "catalog_similar":
                result = catalog_similar(
                    conn,
                    component_id=arguments["component_id"],
                )
            elif name == "catalog_stats":
                result = catalog_stats(conn)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

            return [TextContent(type="text", text=json.dumps(result, default=str))]
        finally:
            conn.close()

    return server


async def main() -> None:
    """Run the MCP server over stdio."""
    if not HAS_MCP:
        print(
            "Error: mcp package is not installed. Install with: pip install mcp>=1.0.0",
            file=sys.stderr,
        )
        sys.exit(1)

    server = _build_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
