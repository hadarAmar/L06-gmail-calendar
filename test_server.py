"""Smoke test for the gmail-calendar MCP server over stdio."""

import asyncio
import os
import shutil
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_DIR = Path(__file__).resolve().parent
UV_BIN = shutil.which("uv") or str(Path.home() / ".local" / "bin" / "uv")
PRIVATE_DIR = os.environ.get(
    "GOOGLE_PRIVATE_DIR", str(Path.home() / "my-private")
)


async def main() -> None:
    """Start the MCP server, list its tools, and call list_events."""
    env = {**os.environ, "GOOGLE_PRIVATE_DIR": PRIVATE_DIR}
    params = StdioServerParameters(
        command=UV_BIN,
        args=["--directory", str(PROJECT_DIR), "run", "gmail-calendar"],
        env=env,
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            print(f"Connected to server: {init.serverInfo.name}")

            tools_result = await session.list_tools()
            print(f"Tools ({len(tools_result.tools)}):")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")

            events_result = await session.call_tool(
                "list_events", {"days_ahead": 1}
            )
            print("\nlist_events(days_ahead=1) result:")
            for item in events_result.content:
                print(getattr(item, "text", item))


if __name__ == "__main__":
    asyncio.run(main())
