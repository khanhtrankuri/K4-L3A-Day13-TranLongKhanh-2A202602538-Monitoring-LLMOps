from __future__ import annotations

from app.dashboard import dashboard_snapshot, render_dashboard_html


def test_dashboard_aggregates_six_required_panels() -> None:
    records = [
        {"event": "request_received"},
        {
            "event": "response_sent",
            "latency_ms": 150,
            "ttft_ms": 50,
            "cost_usd": 0.002,
            "tokens_in": 20,
            "tokens_out": 100,
            "quality_score": 0.9,
            "tool_success": True,
        },
    ]
    payload = dashboard_snapshot(records)
    assert set(payload) >= {"latency", "traffic", "errors", "cost", "tokens", "quality"}
    assert payload["latency"]["p95_ms"] == 150
    assert payload["errors"]["retrieval_success_pct"] == 100
    assert payload["tokens"] == {"input": 20, "output": 100, "threshold_total": 50000}


def test_dashboard_html_exposes_units_time_range_and_thresholds() -> None:
    html = render_dashboard_html()
    for title in ("Latency", "Request traffic", "Error rate", "Cost", "tokens", "Quality"):
        assert title.lower() in html.lower()
    assert "60 minutes" in html
    assert "3000 ms" in html
    assert "30 seconds" in html
