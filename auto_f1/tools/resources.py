"""MCP Resources — URI-addressable F1 data."""

from __future__ import annotations

import asyncio

from mcp.server.fastmcp import FastMCP

from auto_f1.clients import fastf1_client
from auto_f1.clients.openf1 import OpenF1Client
from auto_f1.utils import _json, serialize_df


def register(mcp: FastMCP) -> None:
    """Register MCP resources on the given server instance."""

    @mcp.resource(
        "f1://schedule/{year}",
        name="f1_season_schedule",
        description="F1 season calendar with all Grand Prix events, dates, and circuits",
        mime_type="application/json",
    )
    async def season_schedule(year: int) -> str:
        """Return the race calendar for the given year."""
        df = await asyncio.to_thread(fastf1_client.get_schedule, year)
        records = serialize_df(df)
        return _json(records)

    @mcp.resource(
        "f1://standings",
        name="f1_current_standings",
        description="Current F1 World Championship standings (drivers and constructors)",
        mime_type="application/json",
    )
    async def current_standings() -> str:
        """Return current championship standings from OpenF1."""
        async with OpenF1Client() as client:
            drivers = await client.get_championship_drivers()
            teams = await client.get_championship_teams()
            drivers_info = await client.get_drivers("latest")

        driver_map = {d["driver_number"]: d for d in drivers_info}
        drivers_with_info = []
        for entry in drivers[:20]:
            num = entry.get("driver_number")
            info = driver_map.get(num, {})
            drivers_with_info.append({
                "position": entry.get("position_current"),
                "driver_number": num,
                "driver_name": info.get("full_name", "Unknown"),
                "team_name": info.get("team_name", "Unknown"),
                "points": entry.get("points_current", 0),
            })
        drivers_with_info.sort(key=lambda x: x["points"], reverse=True)
        for i, d in enumerate(drivers_with_info, 1):
            d["position"] = i

        return _json({
            "drivers": drivers_with_info,
            "constructors": teams[:10],
        })
