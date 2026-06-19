"""Comprehensive tests for 100% coverage across all auto_f1 modules."""

from __future__ import annotations

import asyncio
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from auto_f1.utils import _json, serialize_df

# ─────────────────────── Helpers ───────────────────────


def _mock_response(data, status_code=200, headers=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = data
    resp.headers = headers or {}
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        from httpx import HTTPStatusError, Request, Response

        mock_req = MagicMock(spec=Request)
        mock_resp = Response(status_code=status_code, request=mock_req)
        resp.raise_for_status.side_effect = HTTPStatusError(
            message=f"{status_code}", request=mock_req, response=mock_resp
        )
    return resp


def _mock_openf1_client(**methods):
    client = AsyncMock()
    for name, return_value in methods.items():
        setattr(client, name, AsyncMock(return_value=return_value))
    return client


def _patch_openf1_client(methods):
    """Context manager that patches OpenF1Client with given mock methods."""
    mock_client = _mock_openf1_client(**methods)
    cm = patch("auto_f1.tools.openf1_tools.OpenF1Client")
    cls = cm.__enter__()
    cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
    cls.return_value.__aexit__ = AsyncMock(return_value=False)
    return cm, mock_client


def _get_tool_fn(mcp, name):
    for tool in mcp._tool_manager._tools.values():
        if tool.name == name:
            return tool.fn
    raise KeyError(f"Tool {name!r} not found")


def _get_prompt_fn(mcp, name):
    for prompt in mcp._prompt_manager._prompts.values():
        if prompt.name == name:
            return prompt.fn
    raise KeyError(f"Prompt {name!r} not found")


def _get_resource_fn(mcp, uri):
    for key, res in mcp._resource_manager._resources.items():
        if uri in str(key):
            return res.fn
    for tpl in mcp._resource_manager.list_templates():
        if uri in str(tpl.uri_template):
            return tpl.fn
    raise KeyError(f"Resource {uri!r} not found")


def _make_mcp(module):
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("test")
    module.register(mcp)
    return mcp


# ─────────────────────── Utils ───────────────────────


class TestSerializeDf:
    def test_empty_df(self):
        assert serialize_df(pd.DataFrame()) == []

    def test_timedelta_conversion(self):
        df = pd.DataFrame({"time": [timedelta(seconds=90.5)], "name": ["x"]})
        assert serialize_df(df)[0]["time"] == 90.5

    def test_max_rows(self):
        df = pd.DataFrame({"a": [1, 2, 3, 4, 5]})
        assert len(serialize_df(df, max_rows=2)) == 2

    def test_nan_to_none(self):
        df = pd.DataFrame({"a": [1.0, float("nan")]})
        assert pd.isna(serialize_df(df)[1]["a"])

    def test_datetime_column(self):
        df = pd.DataFrame({"d": [datetime(2024, 1, 1, 12, 0, 0)]})
        assert "2024-01-01" in serialize_df(df)[0]["d"]

    def test_mixed_types(self):
        df = pd.DataFrame({
            "time": [timedelta(seconds=1.5)],
            "dt": [datetime(2024, 6, 1)],
            "val": [42.0],
        })
        r = serialize_df(df)
        assert r[0]["time"] == 1.5
        assert r[0]["val"] == 42.0


class TestJson:
    def test_basic(self):
        assert json.loads(_json({"a": 1})) == {"a": 1}

    def test_non_ascii(self):
        assert "赛车" in _json({"name": "赛车"})

    def test_default_str(self):
        assert "2024-01-01" in _json({"dt": datetime(2024, 1, 1)})


# ─────────────────────── OpenF1 Client ───────────────────────


@pytest.mark.asyncio
class TestOpenF1Client:
    async def test_context_manager(self):
        from auto_f1.clients.openf1 import OpenF1Client

        async with OpenF1Client() as client:
            assert client.base_url == "https://api.openf1.org/v1"

    async def test_custom_base_url(self):
        from auto_f1.clients.openf1 import OpenF1Client

        client = OpenF1Client(base_url="http://localhost:8080/")
        assert client.base_url == "http://localhost:8080"
        await client.close()

    async def test_get_success(self):
        from auto_f1.clients.openf1 import OpenF1Client

        async with OpenF1Client() as client:
            with patch.object(client._client, "get", new_callable=AsyncMock, return_value=_mock_response([{"k": "v"}])):
                assert await client._get("/test") == [{"k": "v"}]

    async def test_get_with_params(self):
        from auto_f1.clients.openf1 import OpenF1Client

        async with OpenF1Client() as client:
            with patch.object(client._client, "get", new_callable=AsyncMock, return_value=_mock_response([])) as m:
                await client._get("/test", {"a": 1})
                m.assert_called_once_with("/test", params={"a": 1})

    async def test_get_429_retry_then_success(self):
        from auto_f1.clients.openf1 import OpenF1Client

        rate = _mock_response(None, status_code=429, headers={"Retry-After": "0.01"})
        ok = _mock_response([{"retried": True}])
        call_count = 0

        async def mock_get(path, params=None):
            nonlocal call_count
            call_count += 1
            return rate if call_count == 1 else ok

        async with OpenF1Client() as client:
            with patch.object(client._client, "get", side_effect=mock_get):
                assert await client._get("/test") == [{"retried": True}]

    async def test_get_429_all_retries_exhausted(self):
        from httpx import HTTPStatusError, Request, Response

        from auto_f1.clients.openf1 import OpenF1Client

        async with OpenF1Client() as client:
            resp = MagicMock(status_code=429, headers={})
            req = MagicMock(spec=Request)
            resp.raise_for_status.side_effect = HTTPStatusError(
                message="429", request=req, response=Response(status_code=429, request=req)
            )
            with (
                patch.object(client._client, "get", new_callable=AsyncMock, return_value=resp),
                pytest.raises(HTTPStatusError),
            ):
                await client._get("/test")

    async def test_get_http_error(self):
        from httpx import HTTPStatusError

        from auto_f1.clients.openf1 import OpenF1Client

        async with OpenF1Client() as client:
            with patch.object(client._client, "get", new_callable=AsyncMock, return_value=_mock_response(None, 500)):
                with pytest.raises(HTTPStatusError):
                    await client._get("/test")

    async def test_get_exception_propagates(self):
        from auto_f1.clients.openf1 import OpenF1Client

        async with OpenF1Client() as client:
            with patch.object(client._client, "get", new_callable=AsyncMock, side_effect=ValueError("boom")):
                with pytest.raises(ValueError, match="boom"):
                    await client._get("/test")

    async def _check(self, call, path, expected_params):
        from auto_f1.clients.openf1 import OpenF1Client

        async with OpenF1Client() as client:
            with patch.object(client, "_get", new_callable=AsyncMock, return_value=[]) as m:
                await call(client)
                m.assert_called_once_with(path, expected_params)

    async def test_get_sessions(self):
        await self._check(lambda c: c.get_sessions(year=2025), "/sessions", {"year": 2025})

    async def test_get_drivers(self):
        await self._check(lambda c: c.get_drivers(123), "/drivers", {"session_key": 123})

    async def test_get_positions_no_driver(self):
        await self._check(lambda c: c.get_positions(123), "/position", {"session_key": 123})

    async def test_get_positions_with_driver(self):
        await self._check(
            lambda c: c.get_positions(123, driver_number=44),
            "/position", {"session_key": 123, "driver_number": 44},
        )

    async def test_get_latest_positions(self):
        await self._check(lambda c: c.get_latest_positions(123), "/position", {"session_key": 123})

    async def test_get_laps_no_driver(self):
        await self._check(lambda c: c.get_laps(123), "/laps", {"session_key": 123})

    async def test_get_laps_with_driver(self):
        await self._check(
            lambda c: c.get_laps(123, driver_number=1),
            "/laps", {"session_key": 123, "driver_number": 1},
        )

    async def test_get_car_data_no_speed(self):
        await self._check(
            lambda c: c.get_car_data(123, 1),
            "/car_data", {"session_key": 123, "driver_number": 1},
        )

    async def test_get_car_data_with_speed(self):
        await self._check(
            lambda c: c.get_car_data(123, 1, speed_min=200),
            "/car_data", {"session_key": 123, "driver_number": 1, "speed>=200": ""},
        )

    async def test_get_stints_no_driver(self):
        await self._check(lambda c: c.get_stints(123), "/stints", {"session_key": 123})

    async def test_get_stints_with_driver(self):
        await self._check(
            lambda c: c.get_stints(123, driver_number=44),
            "/stints", {"session_key": 123, "driver_number": 44},
        )

    async def test_get_team_radio_no_driver(self):
        await self._check(lambda c: c.get_team_radio(123), "/team_radio", {"session_key": 123})

    async def test_get_team_radio_with_driver(self):
        await self._check(
            lambda c: c.get_team_radio(123, driver_number=44),
            "/team_radio", {"session_key": 123, "driver_number": 44},
        )

    async def test_get_race_control(self):
        await self._check(lambda c: c.get_race_control(123), "/race_control", {"session_key": 123})

    async def test_get_weather(self):
        await self._check(lambda c: c.get_weather(123), "/weather", {"session_key": 123})

    async def test_get_championship_drivers(self):
        await self._check(
            lambda c: c.get_championship_drivers(),
            "/championship_drivers", {"session_key": "latest"},
        )

    async def test_get_championship_teams(self):
        await self._check(
            lambda c: c.get_championship_teams(),
            "/championship_teams", {"session_key": "latest"},
        )

    async def test_get_current_session(self):
        from auto_f1.clients.openf1 import OpenF1Client

        async with OpenF1Client() as client:
            with patch.object(client, "_get", new_callable=AsyncMock, return_value=[{"key": 1}]):
                assert await client.get_current_session() == {"key": 1}

    async def test_get_current_session_empty(self):
        from auto_f1.clients.openf1 import OpenF1Client

        async with OpenF1Client() as client:
            with patch.object(client, "_get", new_callable=AsyncMock, return_value=[]):
                assert await client.get_current_session() is None

    async def test_get_latest_race_session_found(self):
        from auto_f1.clients.openf1 import OpenF1Client

        sessions = [{"date_start": "2025-06-01", "name": "R1"}, {"date_start": "2025-03-01", "name": "R2"}]
        async with OpenF1Client() as client:
            with patch.object(client, "get_sessions", new_callable=AsyncMock, return_value=sessions):
                assert (await client.get_latest_race_session())["name"] == "R1"

    async def test_get_latest_race_session_empty(self):
        from auto_f1.clients.openf1 import OpenF1Client

        async with OpenF1Client() as client:
            with patch.object(client, "get_sessions", new_callable=AsyncMock, return_value=[]):
                assert await client.get_latest_race_session() is None

    async def test_get_next_race_found(self):
        from auto_f1.clients.openf1 import OpenF1Client

        future = datetime.utcnow().replace(year=datetime.utcnow().year + 1).isoformat() + "Z"
        async with OpenF1Client() as client:
            with patch.object(client, "get_sessions", new_callable=AsyncMock, return_value=[{"date_start": future, "name": "Next"}]):
                assert (await client.get_next_race())["name"] == "Next"

    async def test_get_next_race_not_found(self):
        from auto_f1.clients.openf1 import OpenF1Client

        async with OpenF1Client() as client:
            with patch.object(client, "get_sessions", new_callable=AsyncMock, return_value=[{"date_start": "2000-01-01T00:00:00Z"}]):
                assert await client.get_next_race() is None


# ─────────────────────── FastF1 Client ───────────────────────


class TestFastF1Client:
    @patch("auto_f1.clients.fastf1_client.fastf1")
    def test_setup_cache(self, mock_f1):
        from auto_f1.clients.fastf1_client import setup_cache

        with tempfile.TemporaryDirectory() as d:
            setup_cache(d)
            mock_f1.Cache.enable_cache.assert_called_once_with(d)

    @patch("auto_f1.clients.fastf1_client.fastf1")
    def test_get_session(self, mock_f1):
        from auto_f1.clients.fastf1_client import get_session

        session = MagicMock()
        mock_f1.get_session.return_value = session
        get_session(2024, "Monaco", "R")
        mock_f1.get_session.assert_called_once_with(2024, "Monaco", "R")
        session.load.assert_called_once()

    @pytest.mark.parametrize(
        "fn_name, attr, data",
        [
            ("get_race_results", "results", pd.DataFrame({"Pos": [1]})),
            ("get_laps", "laps", pd.DataFrame({"LapTime": [1.0]})),
            ("get_weather_data", "weather_data", pd.DataFrame({"Temp": [30]})),
        ],
    )
    @patch("auto_f1.clients.fastf1_client.get_session")
    def test_session_attr_returns(self, mock_gs, fn_name, attr, data):
        from auto_f1.clients.fastf1_client import get_laps, get_race_results, get_weather_data

        fn = {"get_race_results": get_race_results, "get_laps": get_laps, "get_weather_data": get_weather_data}[fn_name]
        session = MagicMock()
        setattr(session, attr, data)
        mock_gs.return_value = session
        assert not fn(2024, "Monaco").empty

    @patch("auto_f1.clients.fastf1_client.get_session")
    def test_get_driver_laps(self, mock_gs):
        from auto_f1.clients.fastf1_client import get_driver_laps

        session = MagicMock()
        mock_gs.return_value = session
        get_driver_laps(2024, "Monaco", "VER")
        session.laps.pick_driver.assert_called_once_with("VER")

    @patch("auto_f1.clients.fastf1_client.get_session")
    def test_get_telemetry_fastest(self, mock_gs):
        from auto_f1.clients.fastf1_client import get_telemetry

        session = MagicMock()
        mock_laps = MagicMock()
        mock_laps.pick_driver.return_value = mock_laps
        mock_laps.pick_fastest.return_value.get_telemetry.return_value = pd.DataFrame({"Speed": [300]})
        session.laps = mock_laps
        mock_gs.return_value = session
        get_telemetry(2024, "Monaco", "VER", lap=0)
        mock_laps.pick_fastest.assert_called_once()

    @patch("auto_f1.clients.fastf1_client.get_session")
    def test_get_telemetry_specific_lap(self, mock_gs):
        from auto_f1.clients.fastf1_client import get_telemetry

        session = MagicMock()
        mock_laps = MagicMock()
        mock_lap_row = MagicMock()
        mock_lap_row.get_telemetry.return_value = pd.DataFrame({"Speed": [250]})
        mock_laps.pick_driver.return_value = mock_laps
        mock_laps.__getitem__.return_value.iloc.__getitem__.return_value = mock_lap_row
        session.laps = mock_laps
        mock_gs.return_value = session
        get_telemetry(2024, "Monaco", "VER", lap=2)
        mock_laps.pick_driver.assert_called_with("VER")

    @patch("auto_f1.clients.fastf1_client.fastf1")
    def test_get_schedule(self, mock_f1):
        from auto_f1.clients.fastf1_client import get_schedule

        mock_f1.get_event_schedule.return_value = pd.DataFrame({"Event": ["M"]})
        get_schedule(2024)
        mock_f1.get_event_schedule.assert_called_once_with(2024)

    @patch("auto_f1.clients.fastf1_client.fastf1")
    def test_get_event(self, mock_f1):
        from auto_f1.clients.fastf1_client import get_event

        mock_f1.get_event.return_value = MagicMock()
        get_event(2024, "Monaco")
        mock_f1.get_event.assert_called_once_with(2024, "Monaco")

    @patch("auto_f1.clients.fastf1_client.get_session")
    def test_summarize_session(self, mock_gs):
        from auto_f1.clients.fastf1_client import summarize_session

        session = MagicMock()
        session.event = {"EventName": "Monaco GP", "Circuit": "Circuit de Monaco", "Country": "Monaco"}
        session.total_laps = 78
        session.results = pd.DataFrame({
            "Position": [1, 2, 3],
            "Abbreviation": ["VER", "HAM", "LEC"],
            "FullName": ["Max", "Lewis", "Charles"],
            "TeamName": ["RB", "Merc", "Ferrari"],
            "Points": [25.0, 18.0, 15.0],
            "Status": ["Finished"] * 3,
        })
        mock_gs.return_value = session
        s = summarize_session(2024, "Monaco", "R")
        assert s["event"] == "Monaco GP"
        assert s["total_laps"] == 78
        assert len(s["top_10"]) == 3


# ─────────────────────── Reports / Generator ───────────────────────


def _make_race_data():
    return {
        "session_key": 123,
        "drivers": {1: {"abbr": "VER", "team": "Red Bull", "name": "Max", "number": 1}},
        "final_positions": [{"driver_number": 1, "position": 1}],
        "tire_strategies": {1: [{"compound": "Soft", "lap_start": 1, "lap_end": 20, "tyre_age": 0}]},
        "best_laps": {1: 80.123},
        "race_control_events": [{"message": "SC deployed"}],
        "weather": [{"temp": 30}],
    }


@pytest.mark.asyncio
class TestGatherRaceData:
    async def test_gather_race_data(self):
        from auto_f1.reports.generator import gather_race_data

        mock_client = _mock_openf1_client(
            get_positions=[{"driver_number": 1, "position": 1}, {"driver_number": 44, "position": 2}],
            get_stints=[{"driver_number": 1, "compound": "Soft", "lap_start": 1, "lap_end": 20, "tyre_age_at_start": 0}],
            get_race_control=[{"category": "SafetyCar", "message": "SC"}, {"category": "Other", "message": "x"}],
            get_weather=[{"temp": 30}],
            get_drivers=[{"driver_number": 1, "full_name": "Max", "team_name": "RB", "name_acronym": "VER"}],
            get_laps=[{"driver_number": 1, "lap_duration": 80.5}, {"driver_number": 1, "lap_duration": 79.0}, {"driver_number": 44, "lap_duration": 81.0}],
        )
        with patch("auto_f1.reports.generator.OpenF1Client") as cls:
            cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            cls.return_value.__aexit__ = AsyncMock(return_value=False)
            data = await gather_race_data(123)

        assert data["session_key"] == 123
        assert data["drivers"][1]["name"] == "Max"
        assert data["best_laps"][1] == 79.0
        assert len(data["race_control_events"]) == 1


class TestFormatReportMarkdown:
    def test_full_report(self):
        from auto_f1.reports.generator import format_report_markdown

        report = format_report_markdown(_make_race_data(), ai_analysis="Great race!")
        assert "123" in report and "VER" in report and "Soft(1-20)" in report and "Great race!" in report

    def test_no_events(self):
        from auto_f1.reports.generator import format_report_markdown

        data = {k: [] if isinstance(v, list) else {} if isinstance(v, dict) else v for k, v in _make_race_data().items()}
        data["race_control_events"] = []
        report = format_report_markdown(data)
        assert "F1 Race Report" in report and "Key Events" not in report

    def test_positions_over_20(self):
        from auto_f1.reports.generator import format_report_markdown

        data = _make_race_data()
        data["final_positions"] = [{"driver_number": i, "position": i} for i in range(25)]
        report = format_report_markdown(data)
        rows = [line for line in report.split("\n") if line.startswith("|") and line.split("|")[1].strip().isdigit()]
        assert len(rows) == 20

    def test_no_best_lap(self):
        from auto_f1.reports.generator import format_report_markdown

        data = _make_race_data()
        data["best_laps"] = {}
        assert "VER" in format_report_markdown(data)


class TestSaveReport:
    def test_save_with_filename(self):
        from auto_f1.reports.generator import save_report

        with tempfile.TemporaryDirectory() as d:
            p = save_report("# Test", output_dir=d, filename="t.md")
            assert p.read_text() == "# Test"

    def test_save_auto_filename(self):
        from auto_f1.reports.generator import save_report

        with tempfile.TemporaryDirectory() as d:
            assert save_report("# Auto", output_dir=d).name.startswith("race_report_")


# ─────────────────────── MCP Tools (OpenF1) ───────────────────────


def _test_mcp_tool(module_name, tool_name, fn_args, mock_methods, assertions):
    """Helper to test an MCP tool function."""
    import importlib

    mod = importlib.import_module(f"auto_f1.tools.{module_name}")
    mcp = _make_mcp(mod)
    fn = _get_tool_fn(mcp, tool_name)
    cm, mock_client = _patch_openf1_client(mock_methods) if module_name == "openf1_tools" else (None, None)
    try:
        result = asyncio.get_event_loop().run_until_complete(fn(*fn_args))
        assertions(result, mock_client)
    finally:
        if cm:
            cm.__exit__(None, None, None)


@pytest.mark.asyncio
class TestOpenF1Tools:
    def _make(self, tool_name):
        from auto_f1.tools import openf1_tools

        return _get_tool_fn(_make_mcp(openf1_tools), tool_name)

    async def _call(self, tool_name, mock_methods, *args, **kwargs):
        fn = self._make(tool_name)
        cm, client = _patch_openf1_client(mock_methods)
        try:
            return await fn(*args, **kwargs), client
        finally:
            cm.__exit__(None, None, None)

    async def test_f1_next_race(self):
        result, _ = await self._call("f1_next_race", {"get_next_race": {"name": "Monaco"}})
        assert "Monaco" in result

    async def test_f1_next_race_none(self):
        result, _ = await self._call("f1_next_race", {"get_next_race": None})
        assert "No upcoming race" in result

    async def test_f1_current_standings(self):
        result, client = await self._call(
            "f1_current_standings",
            {
                "get_championship_drivers": [{"driver_number": 1, "position_current": 1, "points_current": 200, "points_start": 0}],
                "get_championship_teams": [{"team": "RB"}],
                "get_drivers": [{"driver_number": 1, "full_name": "Max", "team_name": "RB"}],
            },
        )
        parsed = json.loads(result)
        assert len(parsed["drivers"]) == 1 and parsed["drivers"][0]["driver_name"] == "Max"

    async def test_f1_session_info(self):
        result, _ = await self._call("f1_session_info", {"get_sessions": [{"s": 1}]}, 2025)
        assert len(json.loads(result)) == 1

    async def test_f1_session_info_with_filters(self):
        _, client = await self._call("f1_session_info", {"get_sessions": []}, 2025, country="Monaco", session_type="Race")
        client.get_sessions.assert_called_once_with(year=2025, country_name="Monaco", session_type="Race")

    async def test_f1_race_positions(self):
        result, _ = await self._call(
            "f1_race_positions",
            {"get_positions": [{"driver_number": 1, "position": 2}, {"driver_number": 1, "position": 1}]},
            123,
        )
        parsed = json.loads(result)
        assert len(parsed) == 1 and parsed[0]["position"] == 1

    async def test_f1_driver_laps(self):
        result, _ = await self._call("f1_driver_laps", {"get_laps": [{"lap": 1}, {"lap": 2}]}, 123, 44)
        assert len(json.loads(result)) == 2

    async def test_f1_tire_strategy(self):
        result, _ = await self._call("f1_tire_strategy", {"get_stints": [{"compound": "Soft"}]}, 123)
        assert len(json.loads(result)) == 1

    async def test_f1_race_control_messages(self):
        result, _ = await self._call("f1_race_control_messages", {"get_race_control": [{"message": "SC"}]}, 123)
        assert len(json.loads(result)) == 1

    async def test_f1_weather(self):
        result, _ = await self._call("f1_weather", {"get_weather": [{"temp": 30}] * 15}, 123)
        assert len(json.loads(result)) == 10

    async def test_f1_drivers(self):
        result, _ = await self._call("f1_drivers", {"get_drivers": [{"name": "VER"}]}, 123)
        assert len(json.loads(result)) == 1

    async def test_f1_latest_session_found(self):
        result, _ = await self._call("f1_latest_session", {"get_current_session": {"key": 1}})
        assert json.loads(result)["key"] == 1

    async def test_f1_latest_session_none(self):
        result, _ = await self._call("f1_latest_session", {"get_current_session": None})
        assert "No session" in result

    async def test_f1_team_radio(self):
        result, _ = await self._call("f1_team_radio", {"get_team_radio": [{"clip": "r1"}]}, 123, driver_number=44)
        assert len(json.loads(result)) == 1

    async def test_f1_race_summary_prompt(self):
        result, _ = await self._call(
            "f1_race_summary_prompt",
            {
                "get_positions": [{"driver_number": 1, "position": 1}],
                "get_stints": [{"driver_number": 1, "compound": "Soft", "lap_start": 1, "lap_end": 20, "tyre_age_at_start": 0}],
                "get_race_control": [{"category": "Flag", "message": "Yellow"}],
                "get_weather": [{"temp": 30}],
                "get_drivers": [{"driver_number": 1, "full_name": "VER", "team_name": "RB", "name_acronym": "VER"}],
            },
            123,
        )
        parsed = json.loads(result)
        assert parsed["session_key"] == 123 and "analysis_prompt" in parsed


# ─────────────────────── MCP Tools (FastF1) ───────────────────────


@pytest.mark.asyncio
class TestFastF1Tools:
    def _make(self, tool_name):
        from auto_f1.tools import fastf1_tools

        return _get_tool_fn(_make_mcp(fastf1_tools), tool_name)

    async def test_historical_results(self):
        fn = self._make("f1_historical_results")
        with patch("auto_f1.tools.fastf1_tools.fastf1_client") as c, \
             patch("auto_f1.tools.fastf1_tools.serialize_df", return_value=[{"Pos": 1}]):
            c.get_race_results.return_value = pd.DataFrame()
            result = await fn(2024, "Monaco")
        assert len(json.loads(result)) == 1

    async def test_historical_laps(self):
        fn = self._make("f1_historical_laps")
        with patch("auto_f1.tools.fastf1_tools.fastf1_client") as c, \
             patch("auto_f1.tools.fastf1_tools.serialize_df", return_value=[{"Lap": 1}]):
            c.get_driver_laps.return_value = pd.DataFrame()
            result = await fn(2024, "Monaco", "VER")
        assert len(json.loads(result)) == 1

    async def test_telemetry(self):
        fn = self._make("f1_telemetry")
        with patch("auto_f1.tools.fastf1_tools.fastf1_client") as c, \
             patch("auto_f1.tools.fastf1_tools.serialize_df", return_value=[{"Speed": 300}]):
            c.get_telemetry.return_value = pd.DataFrame()
            result = await fn(2024, "Monaco", "VER", lap=0)
        assert len(json.loads(result)) == 1

    async def test_season_schedule(self):
        fn = self._make("f1_season_schedule")
        with patch("auto_f1.tools.fastf1_tools.fastf1_client") as c, \
             patch("auto_f1.tools.fastf1_tools.serialize_df", return_value=[{"Event": "M"}]):
            c.get_schedule.return_value = pd.DataFrame()
            result = await fn(2024)
        assert len(json.loads(result)) == 1

    async def test_session_summary(self):
        fn = self._make("f1_session_summary")
        with patch("auto_f1.tools.fastf1_tools.fastf1_client") as c:
            c.summarize_session.return_value = {"event": "Monaco GP", "top_10": []}
            result = await fn(2024, "Monaco")
        assert json.loads(result)["event"] == "Monaco GP"


# ─────────────────────── Report Tools ───────────────────────


@pytest.mark.asyncio
class TestReportTools:
    def _make(self, tool_name):
        from auto_f1.tools import report_tools

        return _get_tool_fn(_make_mcp(report_tools), tool_name)

    async def test_gather_race_data(self):
        fn = self._make("f1_gather_race_data")
        data = {"session_key": 123, "drivers": {}}
        with patch("auto_f1.tools.report_tools.gather_race_data", new_callable=AsyncMock, return_value=data):
            assert json.loads(await fn(123))["session_key"] == 123

    async def test_generate_race_report(self):
        fn = self._make("f1_generate_race_report")
        with patch("auto_f1.tools.report_tools.gather_race_data", new_callable=AsyncMock, return_value=_make_race_data()):
            result = await fn(123)
        assert "Race Report" in result and "123" in result


# ─────────────────────── Prompts ───────────────────────


@pytest.mark.asyncio
class TestAnalysisTools:
    def _make(self, tool_name):
        from auto_f1.tools import prompts

        return _get_tool_fn(_make_mcp(prompts), tool_name)

    async def test_f1_race_analysis(self):
        fn = self._make("f1_race_analysis")
        mock_client = _mock_openf1_client(
            get_positions=[{"driver_number": 1, "position": 1}],
            get_stints=[{"driver_number": 1, "compound": "Soft", "lap_start": 1, "lap_end": 20, "tyre_age_at_start": 0}],
            get_race_control=[{"category": "Flag", "message": "Yellow"}],
            get_weather=[{"temp": 30}],
            get_drivers=[{"driver_number": 1, "full_name": "VER", "team_name": "RB", "name_acronym": "VER"}],
        )
        with patch("auto_f1.tools.prompts.OpenF1Client") as cls:
            cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await fn(123)
        assert isinstance(result, str) and "race" in result.lower()

    async def test_f1_race_report(self):
        fn = self._make("f1_race_report")
        with patch("auto_f1.tools.prompts.gather_race_data", new_callable=AsyncMock, return_value=_make_race_data()):
            result = await fn(123)
        assert isinstance(result, str) and "report" in result.lower()


# ─────────────────────── Resources ───────────────────────


@pytest.mark.asyncio
class TestResources:
    def _make(self, uri):
        from auto_f1.tools import resources

        return _get_resource_fn(_make_mcp(resources), uri)

    async def test_season_schedule(self):
        fn = self._make("f1://schedule/")
        with patch("auto_f1.tools.resources.fastf1_client") as c, \
             patch("auto_f1.tools.resources.serialize_df", return_value=[{"Event": "M"}]):
            c.get_schedule.return_value = pd.DataFrame()
            assert len(json.loads(await fn(2024))) == 1

    async def test_current_standings(self):
        fn = self._make("f1://standings")
        mock_client = _mock_openf1_client(
            get_championship_drivers=[{"driver_number": 1, "position_current": 1, "points_current": 200}],
            get_championship_teams=[{"team": "RB"}],
            get_drivers=[{"driver_number": 1, "full_name": "VER", "team_name": "Red Bull"}],
        )
        with patch("auto_f1.tools.resources.OpenF1Client") as cls:
            cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            cls.return_value.__aexit__ = AsyncMock(return_value=False)
            parsed = json.loads(await fn())
        assert len(parsed["drivers"]) == 1


# ─────────────────────── Server ───────────────────────


class TestServer:
    def test_server_module_loads(self):
        from auto_f1.server import mcp

        assert mcp.name == "auto_f1"

    def test_main_calls_run(self):
        from auto_f1.server import main

        with patch("auto_f1.server.mcp") as m:
            main()
            m.run.assert_called_once()

    def test_if_name_main(self):
        import runpy

        with patch("mcp.server.fastmcp.server.FastMCP.run"):
            runpy.run_path(
                str(Path(__file__).parent.parent / "auto_f1" / "server.py"),
                run_name="__main__",
            )
