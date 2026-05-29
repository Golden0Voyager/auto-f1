"""MCP Server for auto_f1 — F1 data tools for AI agents.

Exposes F1 race data, telemetry, standings, and analysis tools
via the Model Context Protocol.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from auto_f1.tools import fastf1_tools, openf1_tools, prompts, report_tools, resources

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "auto_f1",
    instructions="F1 race data, telemetry, standings, and AI analysis",
)

# Register all tool groups
openf1_tools.register(mcp)
fastf1_tools.register(mcp)
report_tools.register(mcp)
resources.register(mcp)
prompts.register(mcp)


def main():
    """Run the auto_f1 MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
