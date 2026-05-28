# Auto F1 🏎️

**AI-Powered F1 Analysis & Real-time Intelligence**

MCP Server + 实时赛况推送 + AI 赛后分析报告

## 架构

```
┌─────────────────────────────────────────────────┐
│                  auto_f1                         │
├──────────────┬──────────────┬───────────────────┤
│  MCP Server  │  AI Reports  │  Live Alerts      │
│  (Hermes/    │  (赛后自动    │  (比赛日实时      │
│   Claude)    │   分析报告)   │   推送)           │
├──────────────┴──────────────┴───────────────────┤
│              Data Layer                          │
├──────────────────┬──────────────────────────────┤
│  OpenF1 API      │  FastF1 Library              │
│  (实时数据)       │  (历史遥测)                   │
│  - 圈速          │  - 完整遥测                   │
│  - 位置          │  - 轮胎数据                   │
│  - 轮胎策略      │  - 天气数据                   │
│  - Race Control  │  - 赛程表                    │
│  - 车队电台      │                              │
└──────────────────┴──────────────────────────────┘
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `f1_next_race` | 下一场比赛信息 |
| `f1_current_standings` | 当前积分榜（车手 + 车队） |
| `f1_session_info` | 查询某年某站的 session |
| `f1_race_positions` | 比赛最终排名 |
| `f1_driver_laps` | 车手逐圈数据 |
| `f1_tire_strategy` | 全场轮胎策略 |
| `f1_race_control_messages` | Race Control 消息（旗/SC/罚时） |
| `f1_weather` | 比赛天气数据 |
| `f1_drivers` | Session 车手列表 |
| `f1_latest_session` | 最新 session |
| `f1_team_radio` | 车队电台 |
| `f1_race_summary_prompt` | AI 分析用的结构化数据 prompt |

## 快速开始

```bash
# 安装
cd ~/Code/auto_f1
uv sync

# 测试 MCP server
uv run auto-f1

# 在 Hermes 中使用
# 添加到 config.yaml 的 mcp servers:
# auto_f1:
#   command: uv
#   args: ["run", "--directory", "/Users/hainingyu/Code/auto_f1", "auto-f1"]
```

## 依赖

- **OpenF1 API** — 免费实时 F1 数据 (https://openf1.org)
- **FastF1** — Python F1 遥测分析库 (https://docs.fastf1.dev/)
- **MCP SDK** — Model Context Protocol

## Roadmap

- [x] MCP Server — 12 个 F1 数据工具
- [ ] 赛事实时监控 + 推送
- [ ] AI 赛后分析报告自动生成
- [ ] 排位赛预测模型
- [ ] 车手对比可视化

## License

MIT
