from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.challenge import resolve_incident
from app.cli import configure_utf8_stdio

BASE_URL = "http://127.0.0.1:8000"


def main() -> None:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scenario",
        choices=["rag_slow", "tool_fail", "cost_spike"],
        help="Chỉ dùng cho practice. Bỏ tham số này để đọc config/challenge.json.",
    )
    parser.add_argument("--disable", action="store_true")
    args = parser.parse_args()

    scenario = resolve_incident(args.scenario)
    path = f"/incidents/{scenario}/disable" if args.disable else f"/incidents/{scenario}/enable"
    try:
        r = httpx.post(f"{BASE_URL}{path}", timeout=10.0)
        r.raise_for_status()
    except httpx.ConnectError:
        print(
            "Lỗi: không kết nối được API tại http://127.0.0.1:8000. "
            "Hãy mở terminal thứ nhất và chạy: "
            "python -m uvicorn app.main:app --reload --env-file .env",
            file=sys.stderr,
        )
        raise SystemExit(1)
    except httpx.HTTPError as exc:
        print(f"Lỗi khi bật/tắt incident: {exc}", file=sys.stderr)
        raise SystemExit(1)

    print(r.status_code, r.json())


if __name__ == "__main__":
    main()
