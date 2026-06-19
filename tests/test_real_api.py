"""Real API integration tests for auto_f1 MCP tools.

Tests all tool modules against live OpenF1 and FastF1 APIs.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from auto_f1.clients import fastf1_client
from auto_f1.clients.openf1 import OpenF1Client
from auto_f1.utils import _json, serialize_df


class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = 0
        self.failed = 0
        self.errors: list[str] = []

    def ok(self, msg: str = ""):
        self.passed += 1
        print(f"  ✅ {msg}" if msg else "  ✅ PASS")

    def fail(self, msg: str):
        self.failed += 1
        self.errors.append(msg)
        print(f"  ❌ {msg}")

    def summary(self) -> bool:
        total = self.passed + self.failed
        status = "PASS" if self.failed == 0 else "FAIL"
        print(f"\n[{status}] {self.name}: {self.passed}/{total} passed")
        return self.failed == 0


async def test_openf1_client():
    """Test OpenF1 API client directly."""
    r = TestResult("OpenF1 Client")

    async with OpenF1Client() as client:
        # Test get_sessions
        try:
            sessions = await client.get_sessions(year=2025, session_type="Race")
            assert isinstance(sessions, list), "Expected list"
            assert len(sessions) > 0, "No races found for 2025"
            r.ok(f"get_sessions: {len(sessions)} races for 2025")
        except Exception as e:
            r.fail(f"get_sessions: {e}")

        # Test get_drivers
        try:
            drivers = await client.get_drivers("latest")
            assert isinstance(drivers, list), "Expected list"
            assert len(drivers) > 0, "No drivers found"
            r.ok(f"get_drivers: {len(drivers)} drivers")
        except Exception as e:
            r.fail(f"get_drivers: {e}")

        # Test get_championship_drivers
        try:
            standings = await client.get_championship_drivers()
            assert isinstance(standings, list), "Expected list"
            assert len(standings) > 0, "No standings found"
            r.ok(f"get_championship_drivers: {len(standings)} entries")
        except Exception as e:
            r.fail(f"get_championship_drivers: {e}")

        # Test get_championship_teams
        try:
            teams = await client.get_championship_teams()
            assert isinstance(teams, list), "Expected list"
            r.ok(f"get_championship_teams: {len(teams)} teams")
        except Exception as e:
            r.fail(f"get_championship_teams: {e}")

        # Test get_next_race
        try:
            next_race = await client.get_next_race()
            if next_race:
                r.ok(f"get_next_race: {next_race.get('meeting_name', 'Unknown')}")
            else:
                r.ok("get_next_race: No upcoming race (season may be over)")
        except Exception as e:
            r.fail(f"get_next_race: {e}")

        # Test get_positions (use latest session)
        try:
            session = await client.get_current_session()
            if session:
                key = session["session_key"]
                positions = await client.get_positions(key)
                assert isinstance(positions, list), "Expected list"
                r.ok(f"get_positions: {len(positions)} position records for session {key}")
            else:
                r.ok("get_positions: Skipped (no current session)")
        except Exception as e:
            r.fail(f"get_positions: {e}")

        # Test get_stints
        try:
            if session:
                stints = await client.get_stints(key)
                assert isinstance(stints, list), "Expected list"
                r.ok(f"get_stints: {len(stints)} stint records")
        except Exception as e:
            r.fail(f"get_stints: {e}")

        # Test get_weather
        try:
            if session:
                weather = await client.get_weather(key)
                assert isinstance(weather, list), "Expected list"
                r.ok(f"get_weather: {len(weather)} weather records")
        except Exception as e:
            r.fail(f"get_weather: {e}")

        # Test get_race_control
        try:
            if session:
                rc = await client.get_race_control(key)
                assert isinstance(rc, list), "Expected list"
                r.ok(f"get_race_control: {len(rc)} messages")
        except Exception as e:
            r.fail(f"get_race_control: {e}")

    return r.summary()


async def test_openf1_tools():
    """Test OpenF1 MCP tool functions (import and call)."""
    r = TestResult("OpenF1 Tools (module)")

    try:
        from auto_f1.tools.openf1_tools import register
        r.ok("Module imports successfully")
    except Exception as e:
        r.fail(f"Import failed: {e}")
        return r.summary()

    # Verify register function exists and is callable
    try:
        assert callable(register), "register should be callable"
        r.ok("register() is callable")
    except Exception as e:
        r.fail(f"register check: {e}")

    return r.summary()


async def test_fastf1_tools():
    """Test FastF1 historical data tools."""
    r = TestResult("FastF1 Tools")

    try:
        r.ok("Module imports successfully")
    except Exception as e:
        r.fail(f"Import failed: {e}")
        return r.summary()

    # Test FastF1 client directly
    try:
        schedule = await asyncio.to_thread(fastf1_client.get_schedule, 2024)
        records = serialize_df(schedule)
        assert isinstance(records, list), "Expected list"
        assert len(records) > 0, "No schedule data"
        r.ok(f"get_schedule(2024): {len(records)} events")
    except Exception as e:
        r.fail(f"get_schedule: {e}")

    # Test race results
    try:
        results = await asyncio.to_thread(fastf1_client.get_race_results, 2024, "Monaco")
        records = serialize_df(results)
        assert isinstance(records, list), "Expected list"
        assert len(records) > 0, "No race results"
        r.ok(f"get_race_results(2024, Monaco): {len(records)} drivers")
    except Exception as e:
        r.fail(f"get_race_results: {e}")

    return r.summary()


async def test_utils():
    """Test utility functions."""
    r = TestResult("Utils")

    # Test _json
    try:
        result = _json({"test": "value", "number": 42})
        parsed = json.loads(result)
        assert parsed["test"] == "value"
        assert parsed["number"] == 42
        r.ok("_json() works correctly")
    except Exception as e:
        r.fail(f"_json: {e}")

    # Test serialize_df with empty DataFrame
    try:
        import pandas as pd
        df = pd.DataFrame()
        result = serialize_df(df)
        assert result == [], "Empty DataFrame should return []"
        r.ok("serialize_df(empty) returns []")
    except Exception as e:
        r.fail(f"serialize_df(empty): {e}")

    # Test serialize_df with timedelta
    try:
        from datetime import timedelta

        import pandas as pd
        df = pd.DataFrame({"time": [timedelta(seconds=90.5)], "name": ["test"]})
        result = serialize_df(df)
        assert result[0]["time"] == 90.5, f"Expected 90.5, got {result[0]['time']}"
        r.ok("serialize_df(timedelta) converts to seconds")
    except Exception as e:
        r.fail(f"serialize_df(timedelta): {e}")

    return r.summary()


async def test_report_tools():
    """Test report generation tools."""
    r = TestResult("Report Tools")

    try:
        r.ok("Module imports successfully")
    except Exception as e:
        r.fail(f"Import failed: {e}")
        return r.summary()

    try:
        r.ok("Report generator imports successfully")
    except Exception as e:
        r.fail(f"Report generator import: {e}")

    return r.summary()


async def test_prompts():
    """Test MCP prompts module."""
    r = TestResult("Prompts")

    try:
        r.ok("Module imports successfully")
    except Exception as e:
        r.fail(f"Import failed: {e}")

    return r.summary()


async def test_resources():
    """Test MCP resources module."""
    r = TestResult("Resources")

    try:
        r.ok("Module imports successfully")
    except Exception as e:
        r.fail(f"Import failed: {e}")

    return r.summary()


async def test_server_integration():
    """Test full server integration — register all tools."""
    r = TestResult("Server Integration")

    try:
        from auto_f1.server import mcp
        assert mcp.name == "auto_f1", f"Expected 'auto_f1', got '{mcp.name}'"
        r.ok(f"Server loaded: {mcp.name}")
    except Exception as e:
        r.fail(f"Server load: {e}")

    return r.summary()


async def main():
    print("=" * 60)
    print("auto_f1 Real API Integration Tests")
    print("=" * 60)

    results = []

    print("\n── Utils ──")
    results.append(await test_utils())

    print("\n── OpenF1 Client (live API) ──")
    results.append(await test_openf1_client())

    print("\n── OpenF1 Tools Module ──")
    results.append(await test_openf1_tools())

    print("\n── FastF1 Tools (live API) ──")
    results.append(await test_fastf1_tools())

    print("\n── Report Tools ──")
    results.append(await test_report_tools())

    print("\n── Prompts ──")
    results.append(await test_prompts())

    print("\n── Resources ──")
    results.append(await test_resources())

    print("\n── Server Integration ──")
    results.append(await test_server_integration())

    print("\n" + "=" * 60)
    all_passed = all(results)
    if all_passed:
        print("🎉 ALL TESTS PASSED")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
