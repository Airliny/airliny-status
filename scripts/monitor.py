#!/usr/bin/env python3
"""Perform real HTTP checks and persist observed status/history; no synthetic data."""
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "monitors.json"
STATUS = ROOT / "data" / "status.json"
HISTORY = ROOT / "data" / "history.json"
UA = "AirlinyStatusMonitor/1.0 (+GitHub Actions; real HTTP health checks)"

def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def check(monitor):
    url = monitor["url"]
    timeout = max(1, min(int(monitor.get("timeout_seconds", 15)), 60))
    expected = set(int(x) for x in monitor.get("expected_status", [200]))
    started = time.perf_counter()
    status = None
    error = None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Cache-Control": "no-cache"}, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status = response.status
                response.read(1024)
        except urllib.error.HTTPError as exc:
            status = exc.code
            exc.read(1024)
        ok = status in expected
    except Exception as exc:
        ok = False
        error = type(exc).__name__ + (": " + str(exc)[:180] if str(exc) else "")
    return {"ok": bool(ok), "http_status": status, "response_ms": round((time.perf_counter()-started)*1000), "error": error}

def main():
    monitors = read_json(CONFIG, [])
    if not isinstance(monitors, list):
        raise SystemExit("config/monitors.json must contain a JSON array")
    old_status = read_json(STATUS, {"monitors": [], "events": []})
    old_by_id = {m.get("id"): m for m in old_status.get("monitors", [])}
    events = old_status.get("events", [])
    history = read_json(HISTORY, {"monitors": {}})
    history.setdefault("monitors", {})
    now = datetime.now(timezone.utc).replace(microsecond=0)
    timestamp = now.isoformat().replace("+00:00", "Z")
    today = now.date().isoformat()
    current = []
    for monitor in monitors:
        for required in ("id", "name", "url"):
            if not monitor.get(required):
                raise SystemExit(f"monitor entry missing {required}: {monitor!r}")
        result = check(monitor)
        item = {**monitor, **result, "last_check": timestamp}
        current.append(item)
        previous = old_by_id.get(monitor["id"])
        if previous and previous.get("last_check") and previous.get("ok") != item["ok"]:
            events.insert(0, {"at": timestamp, "monitor_id": monitor["id"], "name": monitor["name"], "type": "recovered" if item["ok"] else "down", "http_status": item["http_status"], "error": item["error"]})
        records = history["monitors"].setdefault(monitor["id"], [])
        if not records or records[-1].get("date") != today:
            records.append({"date": today, "up": 0, "total": 0})
        day = records[-1]
        day["total"] = int(day.get("total", 0)) + 1
        if item["ok"]:
            day["up"] = int(day.get("up", 0)) + 1
        cutoff = (now.date() - timedelta(days=89)).isoformat()
        history["monitors"][monitor["id"]] = [r for r in records if r.get("date", "") >= cutoff]
    write_json(HISTORY, history)
    write_json(STATUS, {"generated_at": timestamp, "monitors": current, "events": events[:100]})

if __name__ == "__main__":
    main()