# This file is a reference drop-in for the user's separate
# `garmin-connect-mcp` server project. It does NOT run inside outfit-ai-coach.
# For project-side install context (paths, prerequisites, smoke test), see
# `setup/README.md`. The docstring below has the in-file install steps.

"""
Garmin Connect MCP — Training & Performance extensions.

Drop-in additions for the existing garmin_mcp.py server. Adds five tools
that surface training-status / performance / recovery data the original
five tools don't cover:

    - garmin_get_training_status     (productive/maintaining/detraining/etc + fitness age)
    - garmin_get_max_metrics         (VO2 max running + cycling, lactate threshold if present)
    - garmin_get_training_readiness  (0–100 score + level + key drivers)
    - garmin_get_hrv                 (HRV last night + 7-day status)
    - garmin_get_sleep               (sleep duration + stage percentages)

How to install (one-time):

    1. Open projects/garmin-connect-mcp/garmin_mcp.py.
    2. Paste the input-model classes (Section A below) immediately after the
       existing model classes (after BodyCompInput).
    3. Paste the @mcp.tool functions (Section B below) immediately before
       the `if __name__ == "__main__":` block at the bottom of the file.
    4. Restart the MCP server (kill + relaunch via your client, or
       `uv run python garmin_mcp.py` in a terminal for testing).
    5. The five new tools should appear automatically — FastMCP discovers
       them at decoration time.

Library compatibility:

    python-garminconnect exposes these methods on the Garmin client:
        client.get_training_status(date_str)
        client.get_max_metrics(date_str)
        client.get_training_readiness(date_str)
        client.get_hrv_data(date_str)
        client.get_sleep_data(date_str)

    Method names are stable as of python-garminconnect 0.2.x — 0.3.x.
    If a method is missing on your installed version, the tool will return
    an actionable error pointing at the library version mismatch.

Throttling:

    These endpoints are more expensive than the daily-summary endpoint.
    Garmin tends to throttle bursts > ~4 calls/min on the training-status
    family. The skill workflows pace calls (1s between routine pulls, 3s
    for backfill). If you wrap these tools in any loop, add your own
    delay — the MCP server does not.
"""

# ---------------------------------------------------------------------------
# Section A — Input models
# Paste these into garmin_mcp.py after the existing BodyCompInput class.
# ---------------------------------------------------------------------------

# from .garmin_mcp import _StrictModel, ResponseFormat, _validate_iso_date
# (use the existing imports in garmin_mcp.py — these classes live in the same
# file once you paste this in)

class TrainingStatusInput(_StrictModel):  # noqa: F821
    """Input for garmin_get_training_status."""

    target_date: str = Field(  # noqa: F821
        ...,
        description="Date in YYYY-MM-DD format (e.g., '2026-05-31').",
        json_schema_extra={"example": "2026-05-31"},
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)  # noqa: F821

    @field_validator("target_date")  # noqa: F821
    @classmethod
    def _check_date(cls, v: str) -> str:
        return _validate_iso_date(v)  # noqa: F821


class MaxMetricsInput(_StrictModel):  # noqa: F821
    """Input for garmin_get_max_metrics."""

    target_date: str = Field(  # noqa: F821
        ...,
        description="Date in YYYY-MM-DD format. VO2 max is updated periodically; use today's date for the most recent value.",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)  # noqa: F821

    @field_validator("target_date")  # noqa: F821
    @classmethod
    def _check_date(cls, v: str) -> str:
        return _validate_iso_date(v)  # noqa: F821


class TrainingReadinessInput(_StrictModel):  # noqa: F821
    """Input for garmin_get_training_readiness."""

    target_date: str = Field(  # noqa: F821
        ...,
        description="Date in YYYY-MM-DD format. Readiness is computed from overnight recovery — use today's date for this morning's score.",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)  # noqa: F821

    @field_validator("target_date")  # noqa: F821
    @classmethod
    def _check_date(cls, v: str) -> str:
        return _validate_iso_date(v)  # noqa: F821


class HrvInput(_StrictModel):  # noqa: F821
    """Input for garmin_get_hrv."""

    target_date: str = Field(  # noqa: F821
        ...,
        description="Date in YYYY-MM-DD format (the night-of date).",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)  # noqa: F821

    @field_validator("target_date")  # noqa: F821
    @classmethod
    def _check_date(cls, v: str) -> str:
        return _validate_iso_date(v)  # noqa: F821


class SleepInput(_StrictModel):  # noqa: F821
    """Input for garmin_get_sleep."""

    target_date: str = Field(  # noqa: F821
        ...,
        description="Date in YYYY-MM-DD format (the morning-of date — sleep is attributed to the wake-up date by Garmin).",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)  # noqa: F821

    @field_validator("target_date")  # noqa: F821
    @classmethod
    def _check_date(cls, v: str) -> str:
        return _validate_iso_date(v)  # noqa: F821


# ---------------------------------------------------------------------------
# Section B — Tool functions
# Paste these into garmin_mcp.py before the `if __name__ == "__main__":` block.
# ---------------------------------------------------------------------------

# ---- garmin_get_training_status ------------------------------------------

@mcp.tool(  # noqa: F821
    name="garmin_get_training_status",
    annotations={
        "title": "Get Garmin Training Status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def garmin_get_training_status(params: TrainingStatusInput) -> str:
    """Get Garmin's rolling training status classification and fitness age.

    Returns the top-level training status (PRODUCTIVE / MAINTAINING /
    DETRAINING / RECOVERY / UNPRODUCTIVE / PEAKING / OVERREACHING) plus
    a descriptive label, fitness age, and the latest VO2 max reading
    embedded in the same payload.

    Args:
        params (TrainingStatusInput):
            - target_date (str, YYYY-MM-DD)
            - response_format ('markdown'|'json', default 'markdown')

    Returns:
        str: Markdown for humans, or JSON shape:
            {
              "date": "YYYY-MM-DD",
              "training_status": "PRODUCTIVE",
              "training_status_detail": "Building fitness, recovery good",
              "fitness_age": 38,
              "vo2_max_running": 47.0,
              "vo2_max_cycling": 51.0,
              "load_focus": {
                "low_aerobic": 35,
                "high_aerobic": 45,
                "anaerobic": 20
              } | null,
              "weekly_load": 215 | null
            }
    """
    try:
        client = await _get_client()  # noqa: F821
        raw = await asyncio.to_thread(  # noqa: F821
            client.get_training_status, params.target_date
        )
    except AttributeError:
        return (
            "Error: python-garminconnect does not expose get_training_status() on this version. "
            "Upgrade with: uv add 'garminconnect>=0.2.20'. Then restart the MCP server."
        )
    except Exception as e:
        return _handle_error(e)  # noqa: F821

    # The Garmin payload is deeply nested. Pluck the useful fields defensively;
    # different account types (running vs cycling vs multi-sport) return
    # different sub-trees.
    parsed = _parse_training_status(raw, params.target_date)

    if params.response_format == ResponseFormat.JSON:  # noqa: F821
        return json.dumps(parsed, indent=2)  # noqa: F821

    lines = [f"# Training Status — {parsed['date']}", ""]
    status = parsed.get("training_status") or "Unavailable"
    detail = parsed.get("training_status_detail") or ""
    lines.append(f"- **Status**: {status}" + (f" — *{detail}*" if detail else ""))
    if parsed.get("fitness_age") is not None:
        lines.append(f"- **Fitness age**: {parsed['fitness_age']}")
    if parsed.get("vo2_max_running") is not None:
        lines.append(f"- **VO2 max (running)**: {parsed['vo2_max_running']}")
    if parsed.get("vo2_max_cycling") is not None:
        lines.append(f"- **VO2 max (cycling)**: {parsed['vo2_max_cycling']}")
    if parsed.get("weekly_load") is not None:
        lines.append(f"- **Weekly load**: {parsed['weekly_load']}")
    return "\n".join(lines)


def _parse_training_status(raw: dict, target_date: str) -> dict:
    """Pluck the useful fields out of the deeply nested training-status payload."""
    out = {
        "date": target_date,
        "training_status": None,
        "training_status_detail": None,
        "fitness_age": None,
        "vo2_max_running": None,
        "vo2_max_cycling": None,
        "load_focus": None,
        "weekly_load": None,
    }
    if not isinstance(raw, dict):
        return out

    # The payload structure varies; try several known shapes.
    # Shape 1: { "mostRecentTrainingStatus": { "latestTrainingStatusData": { ... } } }
    mrts = raw.get("mostRecentTrainingStatus", {}) or {}
    latest = mrts.get("latestTrainingStatusData", {}) or {}
    if latest:
        # `latest` is keyed by device-id; pick the first device's payload.
        device_payload = next(iter(latest.values()), None)
        if isinstance(device_payload, dict):
            out["training_status"] = device_payload.get("trainingStatus")
            out["training_status_detail"] = device_payload.get("trainingStatusFeedbackPhrase")
            out["fitness_age"] = device_payload.get("fitnessAge")
            out["weekly_load"] = device_payload.get("weeklyTrainingLoad")

    # Shape 2: top-level VO2 max readings live in `mostRecentVO2Max`.
    mrv = raw.get("mostRecentVO2Max", {}) or {}
    if isinstance(mrv, dict):
        gen = mrv.get("generic", {}) or {}
        cyc = mrv.get("cycling", {}) or {}
        out["vo2_max_running"] = gen.get("vo2MaxValue") if gen else None
        out["vo2_max_cycling"] = cyc.get("vo2MaxValue") if cyc else None

    # Shape 3: load focus.
    mrlb = raw.get("mostRecentTrainingLoadBalance", {}) or {}
    mrlb_metric = mrlb.get("metricsTrainingLoadAcuteList") if isinstance(mrlb, dict) else None
    if mrlb_metric:
        latest_lb = mrlb_metric[-1] if isinstance(mrlb_metric, list) else None
        if isinstance(latest_lb, dict):
            out["load_focus"] = {
                "low_aerobic": latest_lb.get("lowAerobicTrainingLoadAcute"),
                "high_aerobic": latest_lb.get("highAerobicTrainingLoadAcute"),
                "anaerobic": latest_lb.get("anaerobicTrainingLoadAcute"),
            }
    return out


# ---- garmin_get_max_metrics ----------------------------------------------

@mcp.tool(  # noqa: F821
    name="garmin_get_max_metrics",
    annotations={
        "title": "Get Garmin Max Metrics (VO2 Max, Lactate Threshold)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def garmin_get_max_metrics(params: MaxMetricsInput) -> str:
    """Get current VO2 max (running + cycling) and lactate threshold if available.

    Lighter-weight than get_training_status when only the VO2 number is needed.

    Returns:
        str: Markdown or JSON shape:
            {
              "date": "YYYY-MM-DD",
              "vo2_max_running": 47.0,
              "vo2_max_cycling": 51.0,
              "lactate_threshold_hr": 162 | null,
              "lactate_threshold_pace_min_per_km": 4.5 | null
            }
    """
    try:
        client = await _get_client()  # noqa: F821
        raw = await asyncio.to_thread(  # noqa: F821
            client.get_max_metrics, params.target_date
        )
    except AttributeError:
        return (
            "Error: python-garminconnect does not expose get_max_metrics() on this version. "
            "Upgrade with: uv add 'garminconnect>=0.2.20'."
        )
    except Exception as e:
        return _handle_error(e)  # noqa: F821

    parsed = _parse_max_metrics(raw, params.target_date)
    if params.response_format == ResponseFormat.JSON:  # noqa: F821
        return json.dumps(parsed, indent=2)  # noqa: F821

    lines = [f"# Max Metrics — {parsed['date']}", ""]
    if parsed.get("vo2_max_running") is not None:
        lines.append(f"- **VO2 max (running)**: {parsed['vo2_max_running']}")
    if parsed.get("vo2_max_cycling") is not None:
        lines.append(f"- **VO2 max (cycling)**: {parsed['vo2_max_cycling']}")
    if parsed.get("lactate_threshold_hr") is not None:
        lines.append(f"- **Lactate threshold HR**: {parsed['lactate_threshold_hr']} bpm")
    if parsed.get("lactate_threshold_pace_min_per_km") is not None:
        lines.append(f"- **Lactate threshold pace**: {parsed['lactate_threshold_pace_min_per_km']} min/km")
    if len(lines) == 2:
        lines.append("- No max metrics returned for this date.")
    return "\n".join(lines)


def _parse_max_metrics(raw, target_date: str) -> dict:
    """Pluck VO2 max + LT fields from get_max_metrics payload."""
    out = {
        "date": target_date,
        "vo2_max_running": None,
        "vo2_max_cycling": None,
        "lactate_threshold_hr": None,
        "lactate_threshold_pace_min_per_km": None,
    }
    if isinstance(raw, list) and raw:
        raw = raw[0]
    if not isinstance(raw, dict):
        return out
    gen = raw.get("generic", {}) or {}
    cyc = raw.get("cycling", {}) or {}
    hr = raw.get("heatAltitudeAcclimation", {}) or {}
    out["vo2_max_running"] = gen.get("vo2MaxValue") if gen else None
    out["vo2_max_cycling"] = cyc.get("vo2MaxValue") if cyc else None
    out["lactate_threshold_hr"] = gen.get("lactateThresholdHeartRate")
    speed_m_s = gen.get("lactateThresholdSpeed")
    if speed_m_s and speed_m_s > 0:
        # m/s → min/km
        out["lactate_threshold_pace_min_per_km"] = round(1000.0 / (speed_m_s * 60.0), 2)
    return out


# ---- garmin_get_training_readiness ---------------------------------------

@mcp.tool(  # noqa: F821
    name="garmin_get_training_readiness",
    annotations={
        "title": "Get Garmin Training Readiness",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def garmin_get_training_readiness(params: TrainingReadinessInput) -> str:
    """Get morning training readiness score (0-100) and contributing factors.

    Best called once per day after wake-up data has uploaded. Returning a stale
    score from yesterday is the most common failure mode if called too early.

    Returns:
        str: Markdown or JSON shape:
            {
              "date": "YYYY-MM-DD",
              "score": 78,
              "level": "MODERATE",  # LOW / MODERATE / HIGH
              "feedback": "...",
              "drivers": {
                "sleep_score": 82,
                "sleep_history": 90,
                "recovery_time_hr": 4,
                "hrv_status": "BALANCED",
                "stress_history": 28,
                "acute_load": 215
              }
            }
    """
    try:
        client = await _get_client()  # noqa: F821
        raw = await asyncio.to_thread(  # noqa: F821
            client.get_training_readiness, params.target_date
        )
    except AttributeError:
        return (
            "Error: python-garminconnect does not expose get_training_readiness() on this version. "
            "Upgrade with: uv add 'garminconnect>=0.2.20'."
        )
    except Exception as e:
        return _handle_error(e)  # noqa: F821

    parsed = _parse_training_readiness(raw, params.target_date)
    if params.response_format == ResponseFormat.JSON:  # noqa: F821
        return json.dumps(parsed, indent=2)  # noqa: F821

    lines = [f"# Training Readiness — {parsed['date']}", ""]
    if parsed.get("score") is not None:
        lines.append(f"- **Score**: {parsed['score']} / 100 — *{parsed.get('level') or '—'}*")
    if parsed.get("feedback"):
        lines.append(f"- **Feedback**: {parsed['feedback']}")
    drivers = parsed.get("drivers") or {}
    if drivers:
        lines.append("")
        lines.append("## Drivers")
        for k, v in drivers.items():
            if v is None:
                continue
            lines.append(f"- {k}: {v}")
    return "\n".join(lines)


def _parse_training_readiness(raw, target_date: str) -> dict:
    """Pluck readiness fields from get_training_readiness payload."""
    out = {
        "date": target_date,
        "score": None,
        "level": None,
        "feedback": None,
        "drivers": {},
    }
    if isinstance(raw, list) and raw:
        # API returns a list of readings; pick the most recent.
        raw = raw[0]
    if not isinstance(raw, dict):
        return out
    out["score"] = raw.get("score")
    out["level"] = raw.get("level")
    out["feedback"] = raw.get("feedbackLong") or raw.get("feedbackShort")
    out["drivers"] = {
        "sleep_score": raw.get("sleepScore"),
        "sleep_history": raw.get("sleepHistory"),
        "recovery_time_hr": raw.get("recoveryTime"),
        "hrv_status": raw.get("hrvWeeklyAverage") and raw.get("hrvStatus"),
        "hrv_weekly_avg": raw.get("hrvWeeklyAverage"),
        "stress_history": raw.get("stressHistory"),
        "acute_load": raw.get("acuteLoad"),
    }
    return out


# ---- garmin_get_hrv ------------------------------------------------------

@mcp.tool(  # noqa: F821
    name="garmin_get_hrv",
    annotations={
        "title": "Get Garmin HRV (overnight + 7-day status)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def garmin_get_hrv(params: HrvInput) -> str:
    """Get overnight HRV and 7-day HRV status (BALANCED / UNBALANCED / LOW / POOR).

    Returns:
        str: Markdown or JSON shape:
            {
              "date": "YYYY-MM-DD",
              "last_night_avg_ms": 62,
              "weekly_avg_ms": 60,
              "status": "BALANCED",
              "baseline_low_ms": 55,
              "baseline_high_ms": 68
            }
    """
    try:
        client = await _get_client()  # noqa: F821
        raw = await asyncio.to_thread(  # noqa: F821
            client.get_hrv_data, params.target_date
        )
    except AttributeError:
        return (
            "Error: python-garminconnect does not expose get_hrv_data() on this version. "
            "Upgrade with: uv add 'garminconnect>=0.2.20'."
        )
    except Exception as e:
        return _handle_error(e)  # noqa: F821

    parsed = _parse_hrv(raw, params.target_date)
    if params.response_format == ResponseFormat.JSON:  # noqa: F821
        return json.dumps(parsed, indent=2)  # noqa: F821

    lines = [f"# HRV — {parsed['date']}", ""]
    if parsed.get("last_night_avg_ms") is not None:
        lines.append(f"- **Last night avg**: {parsed['last_night_avg_ms']} ms")
    if parsed.get("weekly_avg_ms") is not None:
        lines.append(f"- **7-day avg**: {parsed['weekly_avg_ms']} ms")
    if parsed.get("status"):
        lines.append(f"- **Status**: {parsed['status']}")
    if parsed.get("baseline_low_ms") is not None and parsed.get("baseline_high_ms") is not None:
        lines.append(f"- **Personal baseline**: {parsed['baseline_low_ms']}–{parsed['baseline_high_ms']} ms")
    return "\n".join(lines)


def _parse_hrv(raw, target_date: str) -> dict:
    out = {
        "date": target_date,
        "last_night_avg_ms": None,
        "weekly_avg_ms": None,
        "status": None,
        "baseline_low_ms": None,
        "baseline_high_ms": None,
    }
    if not isinstance(raw, dict):
        return out
    summary = raw.get("hrvSummary", {}) or {}
    baseline = summary.get("baseline", {}) or {}
    out["last_night_avg_ms"] = summary.get("lastNightAvg")
    out["weekly_avg_ms"] = summary.get("weeklyAvg")
    out["status"] = summary.get("status")
    out["baseline_low_ms"] = baseline.get("lowUpper")
    out["baseline_high_ms"] = baseline.get("balancedHigh") or baseline.get("upperBalanced")
    return out


# ---- garmin_get_sleep ----------------------------------------------------

@mcp.tool(  # noqa: F821
    name="garmin_get_sleep",
    annotations={
        "title": "Get Garmin Sleep Summary",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def garmin_get_sleep(params: SleepInput) -> str:
    """Get last night's sleep duration and stage breakdown.

    Returns:
        str: Markdown or JSON shape:
            {
              "date": "YYYY-MM-DD",
              "total_sleep_sec": 27720,
              "deep_sec": 3880,
              "light_sec": 14400,
              "rem_sec": 6100,
              "awake_sec": 3340,
              "sleep_score": 82,
              "sleep_quality": "GOOD"
            }
    """
    try:
        client = await _get_client()  # noqa: F821
        raw = await asyncio.to_thread(  # noqa: F821
            client.get_sleep_data, params.target_date
        )
    except AttributeError:
        return (
            "Error: python-garminconnect does not expose get_sleep_data() on this version. "
            "Upgrade with: uv add 'garminconnect>=0.2.20'."
        )
    except Exception as e:
        return _handle_error(e)  # noqa: F821

    parsed = _parse_sleep(raw, params.target_date)
    if params.response_format == ResponseFormat.JSON:  # noqa: F821
        return json.dumps(parsed, indent=2)  # noqa: F821

    lines = [f"# Sleep — {parsed['date']}", ""]
    if parsed.get("total_sleep_sec"):
        lines.append(f"- **Total sleep**: {_format_seconds(parsed['total_sleep_sec'])}")  # noqa: F821
    if parsed.get("deep_sec") is not None:
        lines.append(f"- **Deep**: {_format_seconds(parsed['deep_sec'])}")  # noqa: F821
    if parsed.get("light_sec") is not None:
        lines.append(f"- **Light**: {_format_seconds(parsed['light_sec'])}")  # noqa: F821
    if parsed.get("rem_sec") is not None:
        lines.append(f"- **REM**: {_format_seconds(parsed['rem_sec'])}")  # noqa: F821
    if parsed.get("awake_sec") is not None:
        lines.append(f"- **Awake**: {_format_seconds(parsed['awake_sec'])}")  # noqa: F821
    if parsed.get("sleep_score") is not None:
        qual = parsed.get("sleep_quality") or ""
        lines.append(f"- **Sleep score**: {parsed['sleep_score']}" + (f" — *{qual}*" if qual else ""))
    return "\n".join(lines)


def _parse_sleep(raw, target_date: str) -> dict:
    out = {
        "date": target_date,
        "total_sleep_sec": None,
        "deep_sec": None,
        "light_sec": None,
        "rem_sec": None,
        "awake_sec": None,
        "sleep_score": None,
        "sleep_quality": None,
    }
    if not isinstance(raw, dict):
        return out
    dto = raw.get("dailySleepDTO", {}) or {}
    out["total_sleep_sec"] = dto.get("sleepTimeSeconds")
    out["deep_sec"] = dto.get("deepSleepSeconds")
    out["light_sec"] = dto.get("lightSleepSeconds")
    out["rem_sec"] = dto.get("remSleepSeconds")
    out["awake_sec"] = dto.get("awakeSleepSeconds")
    scores = dto.get("sleepScores", {}) or {}
    overall = scores.get("overall", {}) or {}
    out["sleep_score"] = overall.get("value")
    out["sleep_quality"] = overall.get("qualifierKey")
    return out
