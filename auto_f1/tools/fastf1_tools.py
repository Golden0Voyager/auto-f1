"""FastF1 historical telemetry MCP tools."""

from __future__ import annotations

import asyncio

from mcp.server.fastmcp import FastMCP

from auto_f1.clients import fastf1_client
from auto_f1.utils import _json, serialize_df


def register(mcp: FastMCP) -> None:
    """Register all FastF1 tools on the given MCP server instance."""

    @mcp.tool()
    async def f1_historical_results(year: int, gp: str) -> str:
        """Get race results for a historical Grand Prix (via FastF1).

        Args:
            year: Season year (e.g. 2024).
            gp: Grand Prix name (e.g. 'Monaco', 'Silverstone') or round number.
        """
        df = await asyncio.to_thread(fastf1_client.get_race_results, year, gp)
        records = serialize_df(df)
        return _json(records)

    @mcp.tool()
    async def f1_historical_laps(
        year: int, gp: str, driver: str, session_name: str = "R"
    ) -> str:
        """Get lap data for a specific driver in a historical session (via FastF1).

        Args:
            year: Season year (e.g. 2024).
            gp: Grand Prix name or round number.
            driver: 3-letter driver code (e.g. 'VER', 'HAM', 'LEC').
            session_name: Session type — 'FP1','FP2','FP3','Q','S','SQ','R' (default 'R').
        """
        df = await asyncio.to_thread(
            fastf1_client.get_driver_laps, year, gp, driver, session_name
        )
        records = serialize_df(df, max_rows=90)
        return _json(records)

    @mcp.tool()
    async def f1_telemetry(
        year: int, gp: str, driver: str, lap: int = 0
    ) -> str:
        """Get detailed telemetry for a specific lap (speed, throttle, brake, gear, etc.).

        Args:
            year: Season year (e.g. 2024).
            gp: Grand Prix name or round number.
            driver: 3-letter driver code (e.g. 'VER').
            lap: Lap number (0 = fastest lap, default 0).
        """
        df = await asyncio.to_thread(
            fastf1_client.get_telemetry, year, gp, driver, lap
        )
        records = serialize_df(df)
        return _json(records)

    @mcp.tool()
    async def f1_season_schedule(year: int) -> str:
        """Get the F1 race calendar/schedule for a season (via FastF1).

        Args:
            year: Season year (e.g. 2025).
        """
        df = await asyncio.to_thread(fastf1_client.get_schedule, year)
        records = serialize_df(df)
        return _json(records)

    @mcp.tool()
    async def f1_session_summary(
        year: int, gp: str, session_name: str = "R"
    ) -> str:
        """Get a summary of a historical F1 session — top 10, event info (via FastF1).

        Args:
            year: Season year (e.g. 2024).
            gp: Grand Prix name or round number.
            session_name: Session type (default 'R' for race).
        """
        summary = await asyncio.to_thread(
            fastf1_client.summarize_session, year, gp, session_name
        )
        return _json(summary)
