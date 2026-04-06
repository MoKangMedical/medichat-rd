#!/usr/bin/env python3
"""
SecondMe Develop Skills Auth helper.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import secrets
import sys

import httpx


BASE_URL = "https://app.mindos.com/gate/lab"
PENDING_PATH = Path.home() / ".secondme" / "dev_auth_pending.json"
DEV_CREDENTIALS_PATH = Path.home() / ".secondme" / "dev_credentials"


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.parent.chmod(0o700)
    except OSError:
        pass


def start() -> int:
    code_verifier = secrets.token_urlsafe(32)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode().rstrip("=")
    payload = {
        "codeVerifier": code_verifier,
        "challenge": challenge,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    _ensure_parent(PENDING_PATH)
    PENDING_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    PENDING_PATH.chmod(0o600)
    print(f"https://develop.second.me/auth/skills?challenge={challenge}")
    return 0


def exchange(code: str) -> int:
    if not PENDING_PATH.exists():
        raise SystemExit("Missing ~/.secondme/dev_auth_pending.json. Run `start` first.")
    pending = json.loads(PENDING_PATH.read_text(encoding="utf-8"))
    code_verifier = pending.get("codeVerifier")
    if not code_verifier:
        raise SystemExit("Pending auth file is invalid.")

    with httpx.Client(timeout=30) as client:
        response = client.post(
            f"{BASE_URL}/api/auth/skills/token",
            json={"code": code, "codeVerifier": code_verifier},
        )
    payload = response.json()
    if response.status_code >= 400 or payload.get("code") != 0:
        raise SystemExit(f"Skills Auth exchange failed: HTTP {response.status_code}, payload={payload}")

    data = payload["data"]
    _ensure_parent(DEV_CREDENTIALS_PATH)
    DEV_CREDENTIALS_PATH.write_text(
        json.dumps(
            {
                "accessToken": data["accessToken"],
                "tokenType": data.get("tokenType", "Bearer"),
                "expiresIn": data.get("expiresIn"),
                "updatedAt": datetime.now(timezone.utc).isoformat(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    DEV_CREDENTIALS_PATH.chmod(0o600)
    print("Saved ~/.secondme/dev_credentials")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("start")
    exchange_parser = subparsers.add_parser("exchange")
    exchange_parser.add_argument("--code", required=True)
    args = parser.parse_args()

    if args.command == "start":
        return start()
    if args.command == "exchange":
        return exchange(args.code)
    raise SystemExit(1)


if __name__ == "__main__":
    raise SystemExit(main())
