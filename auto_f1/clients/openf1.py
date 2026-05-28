"""OpenF1 API client — real-time and historical F1 data.

Docs: https://openf1.org/docs
Base URL: https://api.openf1.org/v1
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

BASE_URL = "https://api.openf1.org/v1"
TIMEOUT = 15.0


class OpenF1Client:
    """Async client for the OpenF1 API."""

    def __init__(self, base_url: str = BASE_URL, timeout: float = TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()

    # ── Core endpoints ──────────────────────────────────────────────

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> list[dict]:
        """GET request, returns list of dicts."""
        resp = await self._client.get(path, params=params or {})
        resp.raise_for_status()
        return resp.json()

    # Sessions

    async def get_sessions(self, **filters) -> list[dict]:
        """Get session info (practice, qualifying, race, sprint).

        Filters: year, country_name, session_type, session_key, etc.
        """
        return await self._get("/v1/sessions", filters)

    async def get_current_session(self) -> dict | None:
        """Get the most recent / ongoing session."""
        sessions = await self._get("/v1/sessions", {"session_key": "latest"})
        return sessions[0] if sessions else None

    # Drivers

    async def get_drivers(self, session_key: int | str) -> list[dict]:
        """Get driver list for a session."""
        return await self._get("/v1/drivers", {"session_key": session_key})

    # Positions

    async def get_positions(self, session_key: int | str, driver_number: int | None = None) -> list[dict]:
        """Get position data (historical position changes)."""
        params: dict[str, Any] = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number
        return await self._get("/v1/position", params)

    async def get_latest_positions(self, session_key: int | str) -> list[dict]:
        """Get latest positions for all drivers in a session."""
        params = {"session_key": session_key}
        return await self._get("/v1/position", params)

    # Laps

    async def get_laps(self, session_key: int | str, driver_number: int | None = None) -> list[dict]:
        """Get lap data for a session.

        Returns: lap_number, lap_duration, sector_1/2/3, i1_speed, etc.
        """
        params: dict[str, Any] = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number
        return await self._get("/v1/laps", params)

    # Car data (telemetry)

    async def get_car_data(
        self,
        session_key: int | str,
        driver_number: int,
        speed_min: int | None = None,
    ) -> list[dict]:
        """Get high-frequency car telemetry (~3.7 Hz).

        Returns: speed, throttle, brake, rpm, n_gear, drs, date.
        """
        params: dict[str, Any] = {
            "session_key": session_key,
            "driver_number": driver_number,
        }
        if speed_min is not None:
            params[f"speed>={speed_min}"] = ""
        return await self._get("/v1/car_data", params)

    # Stints (tire strategy)

    async def get_stints(self, session_key: int | str, driver_number: int | None = None) -> list[dict]:
        """Get stint data (tire compound, tire age, lap start/end)."""
        params: dict[str, Any] = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number
        return await self._get("/v1/stints", params)

    # Team radio

    async def get_team_radio(self, session_key: int | str, driver_number: int | None = None) -> list[dict]:
        """Get team radio audio clip metadata."""
        params: dict[str, Any] = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number
        return await self._get("/v1/team_radio", params)

    # Race control messages

    async def get_race_control(self, session_key: int | str) -> list[dict]:
        """Get Race Control messages (flags, safety car, VSC, penalties)."""
        return await self._get("/v1/race_control", {"session_key": session_key})

    # Weather

    async def get_weather(self, session_key: int | str) -> list[dict]:
        """Get weather data for a session."""
        return await self._get("/v1/weather", {"session_key": session_key})

    # Championship standings

    async def get_championship_drivers(self, session_key: int | str = "latest") -> list[dict]:
        """Get driver championship standings."""
        return await self._get("/v1/championship_drivers", {"session_key": session_key})

    async def get_championship_teams(self, session_key: int | str = "latest") -> list[dict]:
        """Get constructor championship standings."""
        return await self._get("/v1/championship_teams", {"session_key": session_key})

    # ── Convenience helpers ─────────────────────────────────────────

    async def get_latest_race_session(self) -> dict | None:
        """Find the most recent race session of the current/last season."""
        year = datetime.now().year
        sessions = await self.get_sessions(year=year, session_type="Race")
        if not sessions:
            sessions = await self.get_sessions(year=year - 1, session_type="Race")
        if not sessions:
            return None
        # Sort by date_start descending, return latest
        sessions.sort(key=lambda s: s.get("date_start", ""), reverse=True)
        return sessions[0]

    async def get_next_race(self) -> dict | None:
        """Get next upcoming race session."""
        now = datetime.utcnow().isoformat() + "Z"
        year = datetime.now().year
        sessions = await self.get_sessions(year=year, session_type="Race")
        for s in sorted(sessions, key=lambda x: x.get("date_start", "")):
            if s.get("date_start", "") > now:
                return s
        return None
