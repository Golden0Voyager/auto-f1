"""MCP Server for auto_f1 — F1 data tools for AI agents.

Exposes F1 race data, telemetry, standings, and analysis tools
via the Model Context Protocol.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from mcp.server.fastmcp import FastMCP

from auto_f1.clients.openf1 import OpenF1Client

logger = logging.getLogger(__name__)

mcp = FastMCP("auto_f1", description="F1 race data, telemetry, standings, and AI analysis")


# ── Helper ──────────────────────────────────────────────────────────

def _json(obj: Any) -> str:
    """Compact JSON serialization."""
    return json.dumps(obj, ensure_ascii=False, default=str)


# ── MCP Tools ───────────────────────────────────────────────────────

@mcp.tool()
async def f1_next_race() -> str:
    """Get information about the next F1 Grand Prix.

    Returns: event name, circuit, country, date, session times.
    """
    async with OpenF1Client() as client:
        race = await client.get_next_race()
        if not race:
            return "No upcoming race found."
        return _json(race)


@mcp.tool()
async def f1_current_standings() -> str:
    """Get current F1 World Championship standings (drivers + constructors).

    Returns both driver and team championship tables.
    """
    async with OpenF1Client() as client:
        drivers = await client.get_championship_drivers()
        teams = await client.get_championship_teams()
        return _json({
            "drivers": drivers[:20],
            "constructors": teams[:10],
            "updated": datetime.utcnow().isoformat() + "Z",
        })


@mcp.tool()
async def f1_session_info(year: int, country: str = "", session_type: str = "") -> str:
    """Get F1 session info for a given year.

    Args:
        year: Season year (e.g. 2025).
        country: Filter by country name (e.g. 'Monaco', 'Italy').
        session_type: Filter by type: 'Practice', 'Qualifying', 'Race', 'Sprint'.
    """
    async with OpenF1Client() as client:
        filters: dict[str, Any] = {"year": year}
        if country:
            filters["country_name"] = country
        if session_type:
            filters["session_type"] = session_type
        sessions = await client.get_sessions(**filters)
        return _json(sessions[:30])


@mcp.tool()
async def f1_race_positions(session_key: int) -> str:
    """Get race positions for a session.

    Args:
        session_key: The OpenF1 session key. Use f1_session_info to find it.
    """
    async with OpenF1Client() as client:
        positions = await client.get_positions(session_key)
        # Get only the latest position per driver
        latest: dict[int, dict] = {}
        for p in positions:
            drv = p.get("driver_number")
            latest[drv] = p
        return _json(list(latest.values()))


@mcp.tool()
async def f1_driver_laps(session_key: int, driver_number: int) -> str:
    """Get lap-by-lap data for a specific driver in a session.

    Args:
        session_key: OpenF1 session key.
        driver_number: F1 driver number (e.g. 1 for Verstappen, 44 for Hamilton).
    """
    async with OpenF1Client() as client:
        laps = await client.get_laps(session_key, driver_number)
        return _json(laps[:50])  # Cap to avoid huge responses


@mcp.tool()
async def f1_tire_strategy(session_key: int) -> str:
    """Get tire strategy (stints) for all drivers in a race.

    Shows which compound each driver used, tire age, and stint laps.
    """
    async with OpenF1Client() as client:
        stints = await client.get_stints(session_key)
        return _json(stints)


@mcp.tool()
async def f1_race_control_messages(session_key: int) -> str:
    """Get Race Control messages for a session.

    Includes: safety car, VSC, red flags, yellow flags, penalties, DRS status.
    """
    async with OpenF1Client() as client:
        messages = await client.get_race_control(session_key)
        return _json(messages)


@mcp.tool()
async def f1_weather(session_key: int) -> str:
    """Get weather data for an F1 session.

    Returns: air temperature, track temperature, humidity, wind, rainfall.
    """
    async with OpenF1Client() as client:
        weather = await client.get_weather(session_key)
        return _json(weather[:10])


@mcp.tool()
async def f1_drivers(session_key: int) -> str:
    """Get the list of drivers for a session.

    Args:
        session_key: OpenF1 session key.
    """
    async with OpenF1Client() as client:
        drivers = await client.get_drivers(session_key)
        return _json(drivers)


@mcp.tool()
async def f1_latest_session() -> str:
    """Get the most recent F1 session (whatever is latest in the database).

    Useful for checking what data is currently available.
    """
    async with OpenF1Client() as client:
        session = await client.get_current_session()
        if not session:
            return "No session found."
        return _json(session)


@mcp.tool()
async def f1_team_radio(session_key: int, driver_number: int | None = None) -> str:
    """Get team radio clips metadata for a session.

    Args:
        session_key: OpenF1 session key.
        driver_number: Optional filter by driver number.
    """
    async with OpenF1Client() as client:
        radio = await client.get_team_radio(session_key, driver_number)
        return _json(radio[:20])


@mcp.tool()
async def f1_race_summary_prompt(session_key: int) -> str:
    """Generate a structured data prompt for AI race analysis.

    Gathers key race data (positions, stints, race control, weather) and
    formats it as a prompt for LLM-based race analysis.
    """
    async with OpenF1Client() as client:
        # Gather all data in parallel
        positions_task = client.get_positions(session_key)
        stints_task = client.get_stints(session_key)
        rc_task = client.get_race_control(session_key)
        weather_task = client.get_weather(session_key)
        drivers_task = client.get_drivers(session_key)

        positions, stints, rc, weather, drivers = await asyncio.gather(
            positions_task, stints_task, rc_task, weather_task, drivers_task
        )

    # Build driver name map
    driver_map: dict[int, dict] = {}
    for d in drivers:
        driver_map[d["driver_number"]] = {
            "name": d.get("full_name", ""),
            "team": d.get("team_name", ""),
            "abbr": d.get("name_acronym", ""),
        }

    # Latest positions
    latest_pos: dict[int, dict] = {}
    for p in positions:
        latest_pos[p["driver_number"]] = p

    # Stint summary per driver
    stint_summary: dict[int, list] = {}
    for s in stints:
        drv = s["driver_number"]
        stint_summary.setdefault(drv, []).append({
            "compound": s.get("compound"),
            "lap_start": s.get("lap_start"),
            "lap_end": s.get("lap_end"),
            "tyre_age": s.get("tyre_age_at_start"),
        })

    # Key RC events
    key_events = [
        m for m in rc
        if m.get("category") in ("Flag", "SafetyCar", "Drs", "CarEvent")
        and m.get("message", "")
    ]

    # Build prompt
    result = {
        "session_key": session_key,
        "drivers": driver_map,
        "final_positions": list(latest_pos.values()),
        "tire_strategies": stint_summary,
        "race_control_events": key_events[:30],
        "weather": weather[:3] if weather else [],
        "analysis_prompt": (
            "Based on the above F1 race data, provide a comprehensive race analysis in Chinese. "
            "Cover: 1) Race winner and podium analysis, 2) Key overtakes and position changes, "
            "3) Tire strategy effectiveness, 4) Safety car / flag impact, "
            "5) Standout performances (driver of the day), 6) Championship implications."
        ),
    }

    return _json(result)


# ── Entry point ─────────────────────────────────────────────────────

def main():
    """Run the auto_f1 MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
