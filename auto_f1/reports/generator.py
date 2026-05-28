"""AI Race Report Generator — post-race analysis powered by LLM."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from auto_f1.clients.openf1 import OpenF1Client


async def gather_race_data(session_key: int) -> dict[str, Any]:
    """Gather comprehensive race data for report generation."""
    async with OpenF1Client() as client:
        import asyncio

        positions_task = client.get_positions(session_key)
        stints_task = client.get_stints(session_key)
        rc_task = client.get_race_control(session_key)
        weather_task = client.get_weather(session_key)
        drivers_task = client.get_drivers(session_key)
        laps_task = client.get_laps(session_key)

        positions, stints, rc, weather, drivers, laps = await asyncio.gather(
            positions_task, stints_task, rc_task, weather_task, drivers_task, laps_task
        )

    # Driver map
    driver_map: dict[int, dict] = {}
    for d in drivers:
        driver_map[d["driver_number"]] = {
            "name": d.get("full_name", ""),
            "team": d.get("team_name", ""),
            "abbr": d.get("name_acronym", ""),
            "number": d["driver_number"],
        }

    # Latest positions
    latest_pos: dict[int, dict] = {}
    for p in positions:
        latest_pos[p["driver_number"]] = p

    # Stint summary
    stint_summary: dict[int, list] = {}
    for s in stints:
        drv = s["driver_number"]
        stint_summary.setdefault(drv, []).append({
            "compound": s.get("compound"),
            "lap_start": s.get("lap_start"),
            "lap_end": s.get("lap_end"),
            "tyre_age": s.get("tyre_age_at_start"),
        })

    # Best lap per driver
    best_laps: dict[int, float] = {}
    for lap in laps:
        drv = lap.get("driver_number")
        dur = lap.get("lap_duration")
        if dur and (drv not in best_laps or dur < best_laps[drv]):
            best_laps[drv] = dur

    # Race control highlights
    key_events = [
        m for m in rc
        if m.get("category") in ("Flag", "SafetyCar", "CarEvent")
        and m.get("message", "")
    ]

    return {
        "session_key": session_key,
        "drivers": driver_map,
        "final_positions": sorted(latest_pos.values(), key=lambda x: x.get("position", 99)),
        "tire_strategies": stint_summary,
        "best_laps": best_laps,
        "race_control_events": key_events[:30],
        "weather": weather[:3] if weather else [],
    }


def format_report_markdown(data: dict[str, Any], ai_analysis: str = "") -> str:
    """Format race data into a Markdown report."""
    drivers = data.get("drivers", {})
    positions = data.get("final_positions", [])
    strategies = data.get("tire_strategies", {})

    lines: list[str] = []
    lines.append(f"# 🏎️ F1 Race Report — Session {data.get('session_key', '?')}")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

    # Results table
    lines.append("## 📊 Race Results\n")
    lines.append("| Pos | Driver | Team | Best Lap |")
    lines.append("|-----|--------|------|----------|")
    for p in positions[:20]:
        drv_num = p.get("driver_number", 0)
        drv_info = drivers.get(drv_num, {})
        pos = p.get("position", "-")
        name = drv_info.get("abbr", f"#{drv_num}")
        team = drv_info.get("team", "?")
        best = data.get("best_laps", {}).get(drv_num)
        best_str = f"{best:.3f}s" if best else "-"
        lines.append(f"| {pos} | {name} | {team} | {best_str} |")

    # Tire strategy
    lines.append("\n## 🔧 Tire Strategy\n")
    for drv_num, stints in strategies.items():
        drv_info = drivers.get(drv_num, {})
        name = drv_info.get("abbr", f"#{drv_num}")
        stint_strs = [f"{s['compound']}({s['lap_start']}-{s['lap_end']})" for s in stints]
        lines.append(f"- **{name}**: {' → '.join(stint_strs)}")

    # Race control
    events = data.get("race_control_events", [])
    if events:
        lines.append("\n## 🚩 Key Events\n")
        for e in events[:15]:
            msg = e.get("message", "")
            lines.append(f"- {msg}")

    # AI analysis section
    if ai_analysis:
        lines.append(f"\n## 🤖 AI Analysis\n\n{ai_analysis}")

    return "\n".join(lines)


def save_report(content: str, output_dir: str | Path = "reports", filename: str = "") -> Path:
    """Save report as Markdown file."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    if not filename:
        filename = f"race_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    path = out / filename
    path.write_text(content, encoding="utf-8")
    return path
