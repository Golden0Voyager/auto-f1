"""F1 analysis tools — race analysis and report generation."""

from __future__ import annotations

import asyncio

from mcp.server.fastmcp import FastMCP

from auto_f1.clients.openf1 import OpenF1Client
from auto_f1.reports.generator import format_report_markdown, gather_race_data
from auto_f1.utils import _json


def register(mcp: FastMCP) -> None:
    """Register analysis tools on the given server instance."""

    @mcp.tool()
    async def f1_race_analysis(session_key: int) -> str:
        """Generate a structured analysis of F1 race data.
        Gathers positions, stints, race control events, and weather data for analysis.
        Args:
            session_key: OpenF1 session key.
        """
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

        stint_summary: dict[int, list[dict]] = {}
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

        return (
            f"Analyze this F1 race data:\n\n{_json(data)}\n\n"
            "Provide a comprehensive race analysis in Chinese. Cover:\n"
            "1) Race winner and podium analysis\n"
            "2) Key overtakes and position changes\n"
            "3) Tire strategy effectiveness\n"
            "4) Safety car / flag impact\n"
            "5) Standout performances (driver of the day)\n"
            "6) Championship implications"
        )

    @mcp.tool()
    async def f1_race_report(session_key: int) -> str:
        """Generate a full Markdown race report for review and enhancement.
        Gathers all race data and formats it as a structured Markdown report.
        Args:
            session_key: OpenF1 session key.
        """
        data = await gather_race_data(session_key)
        report = format_report_markdown(data)

        return (
            f"Review and enhance this F1 race report:\n\n{report}\n\n"
            "Add detailed analysis, driver insights, and strategic commentary."
        )
