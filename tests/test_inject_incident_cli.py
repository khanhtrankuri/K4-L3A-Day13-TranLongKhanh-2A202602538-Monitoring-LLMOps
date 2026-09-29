from __future__ import annotations

import sys

import httpx
import pytest

from scripts import inject_incident


def test_inject_incident_explains_when_api_is_not_running(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["inject_incident.py", "--scenario", "rag_slow"])

    def fail(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(inject_incident.httpx, "post", fail)

    with pytest.raises(SystemExit) as exc_info:
        inject_incident.main()

    assert exc_info.value.code == 1
    output = capsys.readouterr().err
    assert "không kết nối được API" in output
    assert "python -m uvicorn app.main:app" in output
