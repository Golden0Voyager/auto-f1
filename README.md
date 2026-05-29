# Auto F1 🏎️

**AI-Powered F1 Analysis & Real-time Intelligence**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Compatible-orange.svg)](https://modelcontextprotocol.io/)

[中文文档](README.zh-CN.md)

---

## Overview

Auto F1 is a Model Context Protocol (MCP) server that provides AI agents with comprehensive Formula 1 data access — from real-time race telemetry to historical analysis. It combines the [OpenF1 API](https://openf1.org) for live data and [FastF1](https://docs.fastf1.dev/) for historical telemetry.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    auto_f1 MCP Server                │
├──────────────┬──────────────┬───────────────────────┤
│  OpenF1 Tools│  FastF1 Tools│  Reports & Prompts    │
├──────────────┴──────────────┴───────────────────────┤
│                    Data Layer                        │
├────────────────────┬────────────────────────────────┤
│  OpenF1 API        │  FastF1 Library                │
│  (Real-time)       │  (Historical)                  │
│  - Lap times       │  - Full telemetry              │
│  - Positions       │  - Tire data                   │
│  - Tire strategy   │  - Weather                     │
│  - Race Control    │  - Season schedule             │
│  - Team radio      │                                │
└────────────────────┴────────────────────────────────┘
```

## MCP Tools

### OpenF1 Real-time Tools

| Tool | Description |
|------|-------------|
| `f1_next_race` | Get next upcoming race info |
| `f1_current_standings` | Current championship standings (drivers + constructors) |
| `f1_session_info` | Query sessions by year/country/type |
| `f1_race_positions` | Race final positions |
| `f1_driver_laps` | Lap-by-lap data for a driver |
| `f1_tire_strategy` | Tire stints for all drivers |
| `f1_race_control_messages` | Race Control messages (flags, SC, penalties) |
| `f1_weather` | Session weather data |
| `f1_drivers` | Driver list for a session |
| `f1_latest_session` | Most recent session in database |
| `f1_team_radio` | Team radio clip metadata |
| `f1_race_summary_prompt` | Structured data prompt for AI analysis |

### FastF1 Historical Tools

| Tool | Description |
|------|-------------|
| `f1_historical_results` | Race results for any historical GP |
| `f1_historical_laps` | Driver lap data from historical sessions |
| `f1_telemetry` | Detailed telemetry for a specific lap (speed, throttle, brake, gear) |
| `f1_season_schedule` | Full season calendar |
| `f1_session_summary` | Session summary — top 10, event info |

### Report Tools

| Tool | Description |
|------|-------------|
| `f1_gather_race_data` | Gather comprehensive race data for reports |
| `f1_generate_race_report` | Generate full Markdown race report |

### MCP Resources

| URI | Description |
|-----|-------------|
| `f1://schedule/{year}` | Season calendar with all GP events |
| `f1://standings` | Current championship standings |

### MCP Prompts

| Prompt | Description |
|--------|-------------|
| `race_analysis` | Structured prompt for AI race analysis |
| `race_report` | Full Markdown race report as prompt |

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

```bash
git clone https://github.com/Golden0Voyager/auto-f1.git
cd auto-f1
uv sync
uv run auto-f1
```

### Use with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "auto_f1": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/auto-f1", "auto-f1"]
    }
  }
}
```

### Use with Claude Code

```bash
claude mcp add auto_f1 uv run --directory /path/to/auto-f1 auto-f1
```

## Project Structure

```
auto_f1/
├── auto_f1/
│   ├── server.py           # MCP server entry point
│   ├── utils.py            # Shared utilities
│   ├── clients/
│   │   ├── openf1.py       # OpenF1 API client
│   │   └── fastf1_client.py # FastF1 wrapper
│   ├── tools/
│   │   ├── openf1_tools.py # Real-time data tools
│   │   ├── fastf1_tools.py # Historical data tools
│   │   ├── report_tools.py # Report generation
│   │   ├── resources.py    # MCP Resources
│   │   └── prompts.py      # MCP Prompts
│   └── reports/
│       └── generator.py    # Report generator
├── tests/
│   └── test_real_api.py    # Integration tests
├── pyproject.toml
└── README.md
```

## Testing

```bash
uv run python tests/test_real_api.py
```

## Dependencies

| Package | Purpose |
|---------|---------|
| [mcp](https://github.com/modelcontextprotocol/python-sdk) | MCP server framework |
| [httpx](https://github.com/encode/httpx) | Async HTTP client |
| [fastf1](https://docs.fastf1.dev/) | F1 historical telemetry |
| [pandas](https://pandas.pydata.org/) | Data processing |
| [pydantic](https://docs.pydantic.dev/) | Data validation |

## Roadmap

- [x] MCP Server — 17 F1 data tools
- [x] Modular architecture
- [x] Real API integration tests
- [ ] Live race monitoring + push alerts
- [ ] AI post-race analysis report auto-generation
- [ ] Qualifying prediction model
- [ ] Driver comparison visualization

## License

MIT © [Haining Yu](https://github.com/Golden0Voyager)
