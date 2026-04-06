#!/usr/bin/env python3
"""
Prepare and optionally submit a SecondMe external app listing.

Usage:
  python scripts/secondme_apply_listing.py --client-id ... --upload-assets
  python scripts/secondme_apply_listing.py --client-id ... --upload-assets --submit
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any, Dict, Iterable, Optional

from secondme_control_plane import (
    ControlPlaneError,
    api_request,
    list_apps,
    load_dev_token,
    match_app_id,
    upload_cdn_file,
)


DEFAULT_DRAFT_PATH = Path(__file__).resolve().parents[1] / "integrations" / "secondme" / "external-app-listing.draft.json"


def load_draft(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _choose_url(value: Any, *, public_base_url: Optional[str], suffix: Optional[str] = None) -> Optional[str]:
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        return None
    if public_base_url and suffix:
        base = public_base_url.rstrip("/")
        return f"{base}/{suffix.lstrip('/')}"
    for key in ("recommended", "recommendedAfterDeploy", "recommendedAfterPush", "url"):
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate:
            return candidate
    return None


def _upload_local_assets(token: str, entries: Iterable[Dict[str, Any]]) -> list[Dict[str, str]]:
    uploaded: list[Dict[str, str]] = []
    for entry in entries:
        local_path = entry.get("localPath")
        if not local_path:
            continue
        cdn = upload_cdn_file(token, Path(local_path))
        uploaded.append(
            {
                "label": entry.get("label") or Path(local_path).stem,
                "url": cdn["url"],
                "caption": entry.get("caption") or "",
            }
        )
    return uploaded


def build_listing_payload(
    draft: Dict[str, Any],
    *,
    token: Optional[str],
    upload_assets: bool,
    public_base_url: Optional[str],
) -> Dict[str, Any]:
    listing = copy.deepcopy(draft.get("listingDraft") or {})
    screenshots_value = listing.get("screenshots") or []
    icon_value = listing.get("icon") or {}
    og_image_value = listing.get("ogImage") or {}

    screenshot_urls: list[str] = []
    uploaded_screenshots: list[Dict[str, str]] = []
    icon_url: Optional[str] = None
    og_image_url: Optional[str] = None
    if upload_assets:
        if token is None:
            raise ControlPlaneError("--upload-assets requires a valid dev token.")
        uploaded_screenshots = _upload_local_assets(token, screenshots_value)
        screenshot_urls = [entry["url"] for entry in uploaded_screenshots]
        if isinstance(icon_value, dict) and icon_value.get("localPath"):
            icon_url = upload_cdn_file(token, Path(icon_value["localPath"]))["url"]
        if isinstance(og_image_value, dict) and og_image_value.get("localPath"):
            og_image_url = upload_cdn_file(token, Path(og_image_value["localPath"]))["url"]
    else:
        for entry in screenshots_value:
            if isinstance(entry, dict):
                maybe_url = entry.get("url")
                if isinstance(maybe_url, str) and maybe_url:
                    screenshot_urls.append(maybe_url)
        if isinstance(icon_value, dict):
            maybe_icon = icon_value.get("url")
            if isinstance(maybe_icon, str) and maybe_icon:
                icon_url = maybe_icon
        if isinstance(og_image_value, dict):
            maybe_og = og_image_value.get("url")
            if isinstance(maybe_og, str) and maybe_og:
                og_image_url = maybe_og

    website_url = _choose_url(listing.get("websiteUrl"), public_base_url=public_base_url)
    support_url = _choose_url(listing.get("supportUrl"), public_base_url=public_base_url)
    privacy_policy_url = _choose_url(
        listing.get("privacyPolicyUrl"),
        public_base_url=public_base_url,
        suffix="privacy-policy.html",
    )
    app_url = _choose_url(
        listing.get("appUrl"),
        public_base_url=public_base_url,
        suffix="/",
    )

    payload: Dict[str, Any] = {
        "slug": listing.get("slug"),
        "developerName": listing.get("developerName"),
        "subtitle": listing.get("subtitle"),
        "category": listing.get("category"),
        "tags": listing.get("tags") or [],
        "iconUrl": icon_url,
        "ogImageUrl": og_image_url,
        "websiteUrl": website_url,
        "supportUrl": support_url,
        "privacyPolicyUrl": privacy_policy_url,
        "appUrl": app_url,
    }
    if screenshot_urls:
        payload["screenshots"] = screenshot_urls
    return {
        "payload": {key: value for key, value in payload.items() if value not in (None, "", [], {})},
        "uploadedScreenshots": uploaded_screenshots,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft", type=Path, default=DEFAULT_DRAFT_PATH)
    parser.add_argument("--client-id")
    parser.add_argument("--app-id")
    parser.add_argument("--public-base-url")
    parser.add_argument("--upload-assets", action="store_true")
    parser.add_argument("--submit", action="store_true")
    args = parser.parse_args()

    needs_auth = args.upload_assets or args.submit
    token: Optional[str] = None
    matched_app_id: Optional[str] = args.app_id
    if needs_auth:
        token = load_dev_token()
        apps = list_apps(token)
        matched_app_id = match_app_id(apps, client_id=args.client_id, app_id=args.app_id)
    elif not matched_app_id and args.client_id:
        matched_app_id = f"unresolved:clientId:{args.client_id}"

    draft = load_draft(args.draft)

    built = build_listing_payload(
        draft,
        token=token,
        upload_assets=args.upload_assets,
        public_base_url=args.public_base_url,
    )
    result: Dict[str, Any] = {
        "appId": matched_app_id,
        "draftPath": str(args.draft),
        "listingPayload": built["payload"],
        "uploadedScreenshots": built["uploadedScreenshots"],
        "mode": "submit" if args.submit else "dry-run",
    }

    if args.submit:
        if token is None or matched_app_id is None:
            raise ControlPlaneError("Submit mode requires valid auth and a resolved app ID.")
        response = api_request(
            token,
            "POST",
            f"/api/applications/external/{matched_app_id}/apply-listing",
            json_body=built["payload"],
        )
        result["submitResult"] = response

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ControlPlaneError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
