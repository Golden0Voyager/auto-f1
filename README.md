# Auto F1 🏎️

**AI-Powered F1 Analysis & Real-time Intelligence**

AI 驱动的 F1 赛事分析与实时情报系统

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Compatible-orange.svg)](https://modelcontextprotocol.io/)

---

## 🌐 Overview | 概述

Auto F1 is a Model Context Protocol (MCP) server that provides AI agents with comprehensive Formula 1 data access — from real-time race telemetry to historical analysis. It combines the [OpenF1 API](https://openf1.org) for live data and [FastF1](https://docs.fastf1.dev/) for historical telemetry.

Auto F1 是一个 MCP (Model Context Protocol) 服务器，为 AI 智能体提供全面的 F1 数据访问能力 —— 从实时比赛遥测到历史分析。它整合了 [OpenF1 API](https://openf1.org) 的实时数据和 [FastF1](https://docs.fastf1.dev/) 的历史遥测数据。

## 🏗️ Architecture | 架构

```
┌─────────────────────────────────────────────────────┐
│                    auto_f1 MCP Server                │
├──────────────┬──────────────┬───────────────────────┤
│  OpenF1 Tools│  FastF1 Tools│  Reports & Prompts    │
│  (实时数据)   │  (历史遥测)   │  (报告 & 提示词)       │
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

## 🛠️ MCP Tools | 工具列表

### OpenF1 Real-time Tools | 实时数据工具

| Tool | Description (EN) | Description (CN) |
|------|------------------|------------------|
| `f1_next_race` | Get next upcoming race info | 获取下一场比赛信息 |
| `f1_current_standings` | Current championship standings (drivers + constructors) | 当前积分榜（车手 + 车队） |
| `f1_session_info` | Query sessions by year/country/type | 按年份/国家/类型查询赛事 |
| `f1_race_positions` | Race final positions | 比赛最终排名 |
| `f1_driver_laps` | Lap-by-lap data for a driver | 车手逐圈数据 |
| `f1_tire_strategy` | Tire stints for all drivers | 全场轮胎策略 |
| `f1_race_control_messages` | Race Control messages (flags, SC, penalties) | Race Control 消息（旗语/安全车/罚时） |
| `f1_weather` | Session weather data | 比赛天气数据 |
| `f1_drivers` | Driver list for a session | 赛事车手列表 |
| `f1_latest_session` | Most recent session in database | 数据库中最新赛事 |
| `f1_team_radio` | Team radio clip metadata | 车队电台元数据 |
| `f1_race_summary_prompt` | Structured data prompt for AI analysis | AI 分析用结构化数据提示词 |

### FastF1 Historical Tools | 历史数据工具

| Tool | Description (EN) | Description (CN) |
|------|------------------|------------------|
| `f1_historical_results` | Race results for any historical GP | 历史大奖赛比赛结果 |
| `f1_historical_laps` | Driver lap data from historical sessions | 历史赛事车手圈速数据 |
| `f1_telemetry` | Detailed telemetry for a specific lap (speed, throttle, brake, gear) | 特定圈详细遥测（速度/油门/刹车/档位） |
| `f1_season_schedule` | Full season calendar | 赛季完整赛历 |
| `f1_session_summary` | Session summary — top 10, event info | 赛事摘要 — 前十名与赛事信息 |

### Report Tools | 报告工具

| Tool | Description (EN) | Description (CN) |
|------|------------------|------------------|
| `f1_gather_race_data` | Gather comprehensive race data for reports | 汇总比赛综合数据 |
| `f1_generate_race_report` | Generate full Markdown race report | 生成完整 Markdown 比赛报告 |

### MCP Resources | 资源

| URI | Description (EN) | Description (CN) |
|-----|------------------|------------------|
| `f1://schedule/{year}` | Season calendar with all GP events | 赛季赛历（所有大奖赛） |
| `f1://standings` | Current championship standings | 当前积分榜 |

### MCP Prompts | 提示词

| Prompt | Description (EN) | Description (CN) |
|--------|------------------|------------------|
| `race_analysis` | Structured prompt for AI race analysis | AI 赛事分析结构化提示词 |
| `race_report` | Full Markdown race report as prompt | 完整 Markdown 报告提示词 |

## 🚀 Quick Start | 快速开始

### Prerequisites | 前置要求

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

### Installation | 安装

```bash
# Clone the repository | 克隆仓库
git clone https://github.com/Golden0Voyager/auto-f1.git
cd auto-f1

# Install dependencies | 安装依赖
uv sync

# Run the MCP server | 启动 MCP 服务器
uv run auto-f1
```

### Use with Claude Desktop | 在 Claude Desktop 中使用

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

添加到 Claude Desktop MCP 配置文件：

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

### Use with Claude Code | 在 Claude Code 中使用

```bash
# Add MCP server | 添加 MCP 服务器
claude mcp add auto_f1 uv run --directory /path/to/auto-f1 auto-f1
```

## 📁 Project Structure | 项目结构

```
auto_f1/
├── auto_f1/
│   ├── server.py           # MCP server entry point | MCP 服务器入口
│   ├── utils.py            # Shared utilities | 共享工具函数
│   ├── clients/
│   │   ├── openf1.py       # OpenF1 API client | OpenF1 API 客户端
│   │   └── fastf1_client.py # FastF1 wrapper | FastF1 封装
│   ├── tools/
│   │   ├── openf1_tools.py # Real-time data tools | 实时数据工具
│   │   ├── fastf1_tools.py # Historical data tools | 历史数据工具
│   │   ├── report_tools.py # Report generation | 报告生成
│   │   ├── resources.py    # MCP Resources | MCP 资源
│   │   └── prompts.py      # MCP Prompts | MCP 提示词
│   └── reports/
│       └── generator.py    # Report generator | 报告生成器
├── tests/
│   └── test_real_api.py    # Integration tests | 集成测试
├── pyproject.toml
└── README.md
```

## 🧪 Testing | 测试

```bash
# Run integration tests (requires network) | 运行集成测试（需要网络）
uv run python tests/test_real_api.py
```

## 📦 Dependencies | 依赖

| Package | Purpose | 用途 |
|---------|---------|------|
| [mcp](https://github.com/modelcontextprotocol/python-sdk) | MCP server framework | MCP 服务器框架 |
| [httpx](https://github.com/encode/httpx) | Async HTTP client | 异步 HTTP 客户端 |
| [fastf1](https://docs.fastf1.dev/) | F1 historical telemetry | F1 历史遥测数据 |
| [pandas](https://pandas.pydata.org/) | Data processing | 数据处理 |
| [pydantic](https://docs.pydantic.dev/) | Data validation | 数据验证 |

## 🗺️ Roadmap | 路线图

- [x] MCP Server — 17 F1 data tools | MCP 服务器 — 17 个 F1 数据工具
- [x] Modular architecture | 模块化架构
- [x] Real API integration tests | 真实 API 集成测试
- [ ] Live race monitoring + push alerts | 赛事实时监控 + 推送
- [ ] AI post-race analysis report auto-generation | AI 赛后分析报告自动生成
- [ ] Qualifying prediction model | 排位赛预测模型
- [ ] Driver comparison visualization | 车手对比可视化

## 📄 License

MIT © [Haining Yu](https://github.com/Golden0Voyager)
