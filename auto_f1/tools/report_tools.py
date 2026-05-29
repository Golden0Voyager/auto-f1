"""Report generation MCP tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from auto_f1.reports.generator import format_report_markdown, gather_race_data
from auto_f1.utils import _json


def register(mcp: FastMCP) -> None:
    """Register report tools on the given MCP server instance."""

    @mcp.tool()
    async def f1_gather_race_data(session_key: int) -> str:
        """Gather comprehensive race data from OpenF1 for report generation.

        Args:
            session_key: OpenF1 session key.
        """
        data = await gather_race_data(session_key)
        return _json(data)

    @mcp.tool()
    async def f1_generate_race_report(session_key: int) -> str:
        """Generate a full Markdown race report for a session.

        Gathers all race data and formats it as a structured Markdown report.
        Args:
            session_key: OpenF1 session key.
        """
        data = await gather_race_data(session_key)
        report = format_report_markdown(data)
        return report
