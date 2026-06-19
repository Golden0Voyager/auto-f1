"""FastF1 wrapper — historical telemetry and session analysis.

Docs: https://docs.fastf1.dev/
Requires: pip install fastf1
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import fastf1
import pandas as pd

# Cache directory for FastF1 data
_CACHE_DIR = Path(os.getenv("FASTF1_CACHE", Path.home() / ".cache" / "fastf1"))


def setup_cache(dir: Path | str = _CACHE_DIR) -> None:
    """Enable FastF1 cache for faster repeated queries."""
    cache_path = Path(dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_path))


def get_session(year: int, gp: str | int, session_name: str = "R") -> Any:
    """Load an F1 session.

    Args:
        year: Season year (e.g. 2025)
        gp: Grand Prix name or round number (e.g. "Monaco" or 7)
        session_name: 'FP1', 'FP2', 'FP3', 'Q', 'S', 'SQ', 'R'
    """
    setup_cache()
    session = fastf1.get_session(year, gp, session_name)
    session.load()
    return session


def get_race_results(year: int, gp: str | int) -> pd.DataFrame:
    """Get race results as DataFrame.

    Returns: Position, Driver, Team, Points, Laps, Time, Status, etc.
    """
    session = get_session(year, gp, "R")
    return session.results


def get_laps(year: int, gp: str | int, session_name: str = "R") -> pd.DataFrame:
    """Get all lap data for a session.

    Returns: LapTime, Sector1/2/3, SpeedI1/I2/FL/St, Compound, TyreLife, etc.
    """
    session = get_session(year, gp, session_name)
    return session.laps


def get_driver_laps(year: int, gp: str | int, driver: str, session_name: str = "R") -> pd.DataFrame:
    """Get laps for a specific driver (3-letter code, e.g. 'VER')."""
    session = get_session(year, gp, session_name)
    return session.laps.pick_driver(driver)


def get_telemetry(year: int, gp: str | int, driver: str, lap: int = 0) -> pd.DataFrame:
    """Get detailed telemetry for a specific lap.

    Returns: Time, RPM, Speed, nGear, Throttle, Brake, DRS, X, Y, Z, Distance.
    lap=0 means fastest lap.
    """
    session = get_session(year, gp, "R")
    driver_laps = session.laps.pick_driver(driver)
    fastest = driver_laps.pick_fastest() if lap == 0 else driver_laps[driver_laps["LapNumber"] == lap].iloc[0]
    return fastest.get_telemetry()


def get_weather_data(year: int, gp: str | int) -> pd.DataFrame:
    """Get weather data for a race session."""
    session = get_session(year, gp, "R")
    return session.weather_data


def get_schedule(year: int) -> pd.DataFrame:
    """Get the race calendar for a given season."""
    return fastf1.get_event_schedule(year)


def get_event(year: int, gp: str | int) -> Any:
    """Get a single event info."""
    return fastf1.get_event(year, gp)


def summarize_session(year: int, gp: str | int, session_name: str = "R") -> dict:
    """Generate a summary dict of a session for LLM consumption."""
    session = get_session(year, gp, session_name)
    results = session.results

    summary: dict[str, Any] = {
        "event": str(session.event["EventName"]),
        "year": year,
        "session": session_name,
        "circuit": str(session.event["Circuit"]),
        "country": str(session.event["Country"]),
        "total_laps": int(session.total_laps) if hasattr(session, "total_laps") else None,
        "top_10": [],
    }

    for _, row in results.head(10).iterrows():
        summary["top_10"].append({
            "position": int(row["Position"]) if pd.notna(row["Position"]) else None,
            "driver": str(row["Abbreviation"]),
            "driver_name": str(row["FullName"]),
            "team": str(row["TeamName"]),
            "points": float(row["Points"]) if pd.notna(row["Points"]) else 0,
            "status": str(row["Status"]),
        })

    return summary
