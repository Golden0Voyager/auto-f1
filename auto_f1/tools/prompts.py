"""MCP Prompts — structured prompts for F1 analysis."""

from __future__ import annotations

import asyncio

from mcp.server.fastmcp import FastMCP

from auto_f1.clients.openf1 import OpenF1Client
from auto_f1.reports.generator import format_report_markdown, gather_race_data
from auto_f1.utils import _json


def register(mcp: FastMCP) -> None:
    """Register MCP prompts on the given server instance."""

    @mcp.prompt(
        name="race_analysis",
        description="Generate a structured prompt for AI-powered F1 race analysis",
    )
    async def race_analysis(session_key: int) -> list[dict]:
        """Gather race data and return analysis prompt messages."""
        async with OpenF1Client() as client:
            positions_task = client.get_positions(session_key)
            stints_task = client.get_stints(session_key)
            rc_task = client.get_race_control(session_key)
            weather_task = client.get_weather(session_key)
            drivers_task = client.get_drivers(session_key)

            positions, stints, rc, weather, drivers = await asyncio.gather(
                positions_task, stints_task, rc_task, weather_task, drivers_task
            )

        driver_map = {}
        for d in drivers:
            driver_map[d["driver_number"]] = {
                "name": d.get("full_name", ""),
                "team": d.get("team_name", ""),
                "abbr": d.get("name_acronym", ""),
            }

        latest_pos = {}
        for p in positions:
            latest_pos[p["driver_number"]] = p

        stint_summary = {}
        for s in stints:
            drv = s["driver_number"]
            stint_summary.setdefault(drv, []).append({
                "compound": s.get("compound"),
                "lap_start": s.get("lap_start"),
                "lap_end": s.get("lap_end"),
                "tyre_age": s.get("tyre_age_at_start"),
            })

        key_events = [
            m for m in rc
            if m.get("category") in ("Flag", "SafetyCar", "Drs", "CarEvent")
            and m.get("message", "")
        ]

        data = {
            "session_key": session_key,
            "drivers": driver_map,
            "final_positions": list(latest_pos.values()),
            "tire_strategies": stint_summary,
            "race_control_events": key_events[:30],
            "weather": weather[:3] if weather else [],
        }

        return [
            {
                "role": "user",
                "content": (
                    f"Analyze this F1 race data:\n\n{_json(data)}\n\n"
                    "Provide a comprehensive race analysis in Chinese. Cover:\n"
                    "1) Race winner and podium analysis\n"
                    "2) Key overtakes and position changes\n"
                    "3) Tire strategy effectiveness\n"
                    "4) Safety car / flag impact\n"
                    "5) Standout performances (driver of the day)\n"
                    "6) Championship implications"
                ),
            }
        ]

    @mcp.prompt(
        name="race_report",
        description="Generate a full Markdown race report as a prompt",
    )
    async def race_report(session_key: int) -> list[dict]:
        """Gather race data and return a formatted report prompt."""
        data = await gather_race_data(session_key)
        report = format_report_markdown(data)

        return [
            {
                "role": "user",
                "content": (
                    f"Review and enhance this F1 race report:\n\n{report}\n\n"
                    "Add detailed analysis, driver insights, and strategic commentary."
                ),
            }
        ]
