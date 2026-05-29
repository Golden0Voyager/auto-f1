"""Shared utilities for auto_f1 MCP tools."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd


def _json(obj: Any) -> str:
    """Compact JSON serialization."""
    return json.dumps(obj, ensure_ascii=False, default=str)


def serialize_df(df: pd.DataFrame, max_rows: int = 0) -> list[dict]:
    """Convert a DataFrame to a JSON-safe list of dicts.

    Handles FastF1-specific types:
    - Timedelta -> seconds (float)
    - Timestamp -> ISO string
    - NaN -> None
    """
    if df.empty:
        return []

    df = df.copy()

    # Convert timedelta columns to total seconds
    for col in df.select_dtypes(include=["timedelta64"]).columns:
        df[col] = df[col].dt.total_seconds()

    # Convert datetime columns to ISO strings
    for col in df.select_dtypes(include=["datetime64"]).columns:
        df[col] = df[col].dt.strftime("%Y-%m-%dT%H:%M:%S")

    # Replace NaN with None
    df = df.where(pd.notna(df), None)

    if max_rows > 0:
        df = df.head(max_rows)

    return df.to_dict(orient="records")
