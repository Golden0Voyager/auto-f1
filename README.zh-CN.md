# Auto F1 🏎️

**AI 驱动的 F1 赛事分析与实时情报系统**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Compatible-orange.svg)](https://modelcontextprotocol.io/)

[English](README.md)

---

## 概述

Auto F1 是一个 MCP (Model Context Protocol) 服务器，为 AI 智能体提供全面的 F1 数据访问能力 —— 从实时比赛遥测到历史分析。它整合了 [OpenF1 API](https://openf1.org) 的实时数据和 [FastF1](https://docs.fastf1.dev/) 的历史遥测数据。

## 架构

```
┌─────────────────────────────────────────────────────┐
│                    auto_f1 MCP Server                │
├──────────────┬──────────────┬───────────────────────┤
│  OpenF1 工具  │  FastF1 工具  │  报告 & 提示词        │
├──────────────┴──────────────┴───────────────────────┤
│                    数据层                            │
├────────────────────┬────────────────────────────────┤
│  OpenF1 API        │  FastF1 库                     │
│  (实时数据)         │  (历史数据)                     │
│  - 圈速            │  - 完整遥测                     │
│  - 位置            │  - 轮胎数据                     │
│  - 轮胎策略        │  - 天气数据                     │
│  - Race Control    │  - 赛程表                      │
│  - 车队电台        │                                │
└────────────────────┴────────────────────────────────┘
```

## MCP 工具

### OpenF1 实时数据工具

| 工具 | 说明 |
|------|------|
| `f1_next_race` | 获取下一场比赛信息 |
| `f1_current_standings` | 当前积分榜（车手 + 车队） |
| `f1_session_info` | 按年份/国家/类型查询赛事 |
| `f1_race_positions` | 比赛最终排名 |
| `f1_driver_laps` | 车手逐圈数据 |
| `f1_tire_strategy` | 全场轮胎策略 |
| `f1_race_control_messages` | Race Control 消息（旗语/安全车/罚时） |
| `f1_weather` | 比赛天气数据 |
| `f1_drivers` | 赛事车手列表 |
| `f1_latest_session` | 数据库中最新赛事 |
| `f1_team_radio` | 车队电台元数据 |
| `f1_race_summary_prompt` | AI 分析用结构化数据提示词 |

### FastF1 历史数据工具

| 工具 | 说明 |
|------|------|
| `f1_historical_results` | 历史大奖赛比赛结果 |
| `f1_historical_laps` | 历史赛事车手圈速数据 |
| `f1_telemetry` | 特定圈详细遥测（速度/油门/刹车/档位） |
| `f1_season_schedule` | 赛季完整赛历 |
| `f1_session_summary` | 赛事摘要 — 前十名与赛事信息 |

### 报告工具

| 工具 | 说明 |
|------|------|
| `f1_gather_race_data` | 汇总比赛综合数据 |
| `f1_generate_race_report` | 生成完整 Markdown 比赛报告 |

### MCP 资源

| URI | 说明 |
|-----|------|
| `f1://schedule/{year}` | 赛季赛历（所有大奖赛） |
| `f1://standings` | 当前积分榜 |

### MCP 提示词

| 提示词 | 说明 |
|--------|------|
| `race_analysis` | AI 赛事分析结构化提示词 |
| `race_report` | 完整 Markdown 报告提示词 |

## 快速开始

### 前置要求

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) 包管理器

### 安装

```bash
git clone https://github.com/Golden0Voyager/auto-f1.git
cd auto-f1
uv sync
uv run auto-f1
```

### 在 Claude Desktop 中使用

添加到 Claude Desktop MCP 配置文件（`claude_desktop_config.json`）：

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

### 在 Claude Code 中使用

```bash
claude mcp add auto_f1 uv run --directory /path/to/auto-f1 auto-f1
```

## 项目结构

```
auto_f1/
├── auto_f1/
│   ├── server.py           # MCP 服务器入口
│   ├── utils.py            # 共享工具函数
│   ├── clients/
│   │   ├── openf1.py       # OpenF1 API 客户端
│   │   └── fastf1_client.py # FastF1 封装
│   ├── tools/
│   │   ├── openf1_tools.py # 实时数据工具
│   │   ├── fastf1_tools.py # 历史数据工具
│   │   ├── report_tools.py # 报告生成
│   │   ├── resources.py    # MCP 资源
│   │   └── prompts.py      # MCP 提示词
│   └── reports/
│       └── generator.py    # 报告生成器
├── tests/
│   └── test_real_api.py    # 集成测试
├── pyproject.toml
└── README.md
```

## 测试

```bash
uv run python tests/test_real_api.py
```

## 依赖

| 包 | 用途 |
|----|------|
| [mcp](https://github.com/modelcontextprotocol/python-sdk) | MCP 服务器框架 |
| [httpx](https://github.com/encode/httpx) | 异步 HTTP 客户端 |
| [fastf1](https://docs.fastf1.dev/) | F1 历史遥测数据 |
| [pandas](https://pandas.pydata.org/) | 数据处理 |
| [pydantic](https://docs.pydantic.dev/) | 数据验证 |

## 路线图

- [x] MCP 服务器 — 17 个 F1 数据工具
- [x] 模块化架构
- [x] 真实 API 集成测试
- [ ] 赛事实时监控 + 推送
- [ ] AI 赛后分析报告自动生成
- [ ] 排位赛预测模型
- [ ] 车手对比可视化

## 许可证

MIT © [Haining Yu](https://github.com/Golden0Voyager)
