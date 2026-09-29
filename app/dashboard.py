from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from .logging_config import LOG_PATH
from .metrics import percentile


def load_recent_records(
    path: Path = LOG_PATH, *, minutes: int = 60, now: datetime | None = None
) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(minutes=minutes)
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
            timestamp = datetime.fromisoformat(str(record["ts"]).replace("Z", "+00:00"))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            continue
        if timestamp >= cutoff:
            records.append(record)
    return records


def _numbers(records: Iterable[dict[str, Any]], field: str) -> list[float]:
    return [
        float(record[field])
        for record in records
        if isinstance(record.get(field), (int, float))
    ]


def dashboard_snapshot(records: list[dict[str, Any]]) -> dict[str, Any]:
    received = [item for item in records if item.get("event") == "request_received"]
    failed = [item for item in records if item.get("event") == "request_failed"]
    responses = [item for item in records if item.get("event") == "response_sent"]
    latencies = [int(value) for value in _numbers(responses, "latency_ms")]
    ttfts = [int(value) for value in _numbers(responses, "ttft_ms")]
    tool_results = [item["tool_success"] for item in records if item.get("tool_success") is not None]
    costs = _numbers(responses, "cost_usd")
    qualities = _numbers(responses, "quality_score")
    error_types = Counter(str(item.get("error_type", "unknown")) for item in failed)

    return {
        "time_range_minutes": 60,
        "refresh_seconds": 30,
        "latency": {
            "p50_ms": percentile(latencies, 50),
            "p95_ms": percentile(latencies, 95),
            "p99_ms": percentile(latencies, 99),
            "ttft_p95_ms": percentile(ttfts, 95),
            "threshold_ms": 3000,
        },
        "traffic": {
            "requests": len(received),
            "requests_per_minute": round(len(received) / 60, 2),
            "threshold_requests_per_minute": 1,
        },
        "errors": {
            "error_rate_pct": round(100 * len(failed) / len(received), 2) if received else 0,
            "retrieval_success_pct": round(100 * sum(tool_results) / len(tool_results), 2)
            if tool_results
            else 0,
            "breakdown": dict(error_types),
            "error_rate_threshold_pct": 2,
        },
        "cost": {"total_usd": round(sum(costs), 6), "threshold_usd": 2.5},
        "tokens": {
            "input": int(sum(_numbers(responses, "tokens_in"))),
            "output": int(sum(_numbers(responses, "tokens_out"))),
            "threshold_total": 50000,
        },
        "quality": {
            "average": round(mean(qualities), 3) if qualities else 0,
            "threshold": 0.75,
        },
    }


def render_dashboard_html() -> str:
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>K4-L3A Monitoring Dashboard</title>
<style>
:root{font-family:Inter,system-ui,sans-serif;color:#e8eef8;background:#09111f}body{margin:0;padding:28px;background:radial-gradient(circle at top right,#17325a,#09111f 45%)}
header{display:flex;justify-content:space-between;align-items:end;margin-bottom:22px}h1{margin:0;font-size:26px}.meta{color:#9bb0cc;font-size:13px}
.grid{display:grid;grid-template-columns:repeat(3,minmax(240px,1fr));gap:16px}.panel{background:#111d30;border:1px solid #263955;border-radius:14px;padding:18px;box-shadow:0 12px 30px #0004}
.panel h2{font-size:15px;color:#a9bdd7;margin:0 0 14px}.value{font-size:28px;font-weight:750;color:#fff}.detail{line-height:1.75;color:#c7d5e7;font-size:13px}.threshold{margin-top:12px;padding-top:10px;border-top:1px solid #2a3a51;color:#72d7b2;font-size:12px}
@media(max-width:900px){.grid{grid-template-columns:1fr 1fr}}@media(max-width:600px){.grid{grid-template-columns:1fr}}
</style></head><body><header><div><h1>Monitoring &amp; LLMOps</h1><div class="meta">K4-L3A · source: data/logs.jsonl</div></div><div class="meta">Time range: 60 minutes · Refresh: 30 seconds</div></header>
<main class="grid">
<section class="panel"><h2>Latency percentiles &amp; TTFT</h2><div class="value" id="latency">—</div><div class="detail" id="latencyDetail"></div><div class="threshold">SLO: P95 ≤ 3000 ms</div></section>
<section class="panel"><h2>Request traffic</h2><div class="value" id="traffic">—</div><div class="detail">requests in the last 60 minutes</div><div class="threshold">Reference: ≥ 1 request/minute</div></section>
<section class="panel"><h2>Error rate &amp; retrieval success</h2><div class="value" id="errors">—</div><div class="detail" id="errorsDetail"></div><div class="threshold">Guardrails: errors ≤ 2% · retrieval ≥ 90%</div></section>
<section class="panel"><h2>Cost over time</h2><div class="value" id="cost">—</div><div class="detail">total estimated model cost</div><div class="threshold">Budget: ≤ $2.50 / window</div></section>
<section class="panel"><h2>Input &amp; output tokens</h2><div class="value" id="tokens">—</div><div class="detail" id="tokensDetail"></div><div class="threshold">Reference: ≤ 50,000 tokens / window</div></section>
<section class="panel"><h2>Quality proxy</h2><div class="value" id="quality">—</div><div class="detail">heuristic score from 0 to 1</div><div class="threshold">Guardrail: mean ≥ 0.75</div></section>
</main><script>
async function refresh(){const d=await fetch('/dashboard/data').then(r=>r.json());
latency.textContent=d.latency.p95_ms.toFixed(0)+' ms P95';latencyDetail.textContent=`P50 ${d.latency.p50_ms.toFixed(0)} · P99 ${d.latency.p99_ms.toFixed(0)} · TTFT P95 ${d.latency.ttft_p95_ms.toFixed(0)} ms`;
traffic.textContent=d.traffic.requests;errors.textContent=d.errors.error_rate_pct.toFixed(2)+'% errors';errorsDetail.textContent=`Retrieval success ${d.errors.retrieval_success_pct.toFixed(2)}%`;
cost.textContent='$'+d.cost.total_usd.toFixed(4);tokens.textContent=(d.tokens.input+d.tokens.output).toLocaleString();tokensDetail.textContent=`Input ${d.tokens.input.toLocaleString()} · Output ${d.tokens.output.toLocaleString()}`;
quality.textContent=d.quality.average.toFixed(2);}
refresh();setInterval(refresh,30000);
</script></body></html>"""
