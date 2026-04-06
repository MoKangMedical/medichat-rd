#!/usr/bin/env python3
"""
Update a SecondMe external app's core metadata.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from secondme_control_plane import (
    ControlPlaneError,
    api_request,
    list_apps,
    load_dev_token,
    match_app_id,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-id")
    parser.add_argument("--app-id")
    parser.add_argument("--app-name")
    parser.add_argument("--app-description")
    parser.add_argument("--redirect-uri", action="append", dest="redirect_uris")
    parser.add_argument("--scope", action="append", dest="scopes")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not any([args.app_name, args.app_description, args.redirect_uris, args.scopes]):
        raise ControlPlaneError("Provide at least one field to update.")

    if args.dry_run:
        resolved_app_id = args.app_id or (f"unresolved:clientId:{args.client_id}" if args.client_id else None)
        if not resolved_app_id:
            raise ControlPlaneError("Dry-run mode requires --app-id or --client-id.")
    else:
        token = load_dev_token()
        apps = list_apps(token)
        resolved_app_id = match_app_id(apps, client_id=args.client_id, app_id=args.app_id)

    payload = {}
    if args.app_name:
        payload["appName"] = args.app_name
    if args.app_description:
        payload["appDescription"] = args.app_description
    if args.redirect_uris:
        payload["redirectUris"] = args.redirect_uris
    if args.scopes:
        payload["allowedScopes"] = args.scopes

    result = {
        "appId": resolved_app_id,
        "payload": payload,
        "mode": "dry-run" if args.dry_run else "submit",
    }

    if not args.dry_run:
        response = api_request(
            token,
            "POST",
            f"/api/applications/external/{resolved_app_id}/update",
            json_body=payload,
        )
        result["updateResult"] = response

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ControlPlaneError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
