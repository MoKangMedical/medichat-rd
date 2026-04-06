#!/usr/bin/env python3
"""
Create or update a SecondMe integration from a local manifest template.

This script expects a valid Skills Auth token at ~/.secondme/dev_credentials.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any, Dict, Optional

from secondme_control_plane import (
    ControlPlaneError,
    api_request,
    list_apps,
    list_integrations,
    load_dev_token,
    match_app_id,
)


DEFAULT_MANIFEST_PATH = Path(__file__).resolve().parents[1] / "integrations" / "secondme" / "medichat-rd.manifest.json"


def load_manifest_template(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def prepare_manifest_payload(template: Dict[str, Any], *, endpoint: str, app_id: str) -> Dict[str, Any]:
    payload = copy.deepcopy(template)
    payload["manifest"]["mcp"]["endpoint"] = endpoint
    payload["manifest"]["envBindings"]["release"]["endpoint"] = endpoint
    payload["manifest"]["oauth"]["appId"] = app_id
    return payload


def find_integration_id(integrations: list[Dict[str, Any]], *, skill_key: str) -> Optional[str]:
    for integration in integrations:
        manifest = integration.get("manifest") or {}
        skill = manifest.get("skill") or {}
        if (
            skill.get("key") == skill_key
            or integration.get("integrationKey") == skill_key
            or integration.get("skillKey") == skill_key
        ):
            return integration.get("integrationId") or integration.get("id")
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--client-id")
    parser.add_argument("--app-id")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()

    template = load_manifest_template(args.manifest)
    skill_key = template["manifest"]["skill"]["key"]
    if args.dry_run:
        if args.app_id:
            matched_app_id = args.app_id
        elif args.client_id:
            matched_app_id = f"unresolved:clientId:{args.client_id}"
        else:
            raise ControlPlaneError("Dry-run mode still requires --app-id or --client-id.")
        payload = prepare_manifest_payload(template, endpoint=args.endpoint, app_id=matched_app_id)
        print(
            json.dumps(
                {
                    "mode": "dry-run",
                    "skillKey": skill_key,
                    "appId": matched_app_id,
                    "manifestPayload": payload,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    token = load_dev_token()
    apps = list_apps(token)
    matched_app_id = match_app_id(apps, client_id=args.client_id, app_id=args.app_id)
    payload = prepare_manifest_payload(template, endpoint=args.endpoint, app_id=matched_app_id)

    integrations = list_integrations(token)
    integration_id = find_integration_id(integrations, skill_key=skill_key)

    if integration_id:
        saved = api_request(token, "POST", f"/api/integrations/{integration_id}/update", json_body=payload)
        operation = "updated"
    else:
        saved = api_request(token, "POST", "/api/integrations/create", json_body=payload)
        integration_id = saved.get("integrationId") or saved.get("id")
        operation = "created"

    if not integration_id:
        raise ControlPlaneError("Integration save succeeded but no integration ID was returned.")

    validation = api_request(token, "POST", f"/api/integrations/{integration_id}/validate", json_body={})
    result = {
        "operation": operation,
        "integrationId": integration_id,
        "appId": matched_app_id,
        "skillKey": skill_key,
        "validation": validation,
    }

    if args.release:
        release = api_request(token, "POST", f"/api/integrations/{integration_id}/release", json_body={})
        result["release"] = release

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ControlPlaneError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
