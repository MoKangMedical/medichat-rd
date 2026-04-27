"""
Traffic analytics API.

目标：
- 记录前端页面访问事件
- 聚合每日访问量、独立访客和国家分布
- 为后台页面提供可直接渲染的访问分析数据
"""

from __future__ import annotations

import hashlib
import ipaddress
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import httpx
from fastapi import APIRouter, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/v1/analytics", tags=["访问分析"])

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "traffic_analytics.db"
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")
PLATFORM_ADMIN_TOKEN = os.getenv("PLATFORM_ADMIN_TOKEN", "").strip()

COUNTRY_CACHE: dict[str, tuple[str, str]] = {}
TWITTER_REFERRER_HOSTS = (
    "x.com",
    "twitter.com",
    "t.co",
    "mobile.twitter.com",
    "m.twitter.com",
)
HIGH_INTENT_PAGE_IDS = {
    "doctor": "医生助手",
    "genomic-hub": "基因与登记",
    "scientific-skills": "科研加速",
    "disease-research": "疾病研究",
    "drug-research": "药物线索",
}
LEAD_EVENT_TYPES = ("partner_inquiry", "demo_request", "contact_click")

COUNTRY_DISPLAY_NAMES = {
    "AU": "澳大利亚",
    "CA": "加拿大",
    "CH": "瑞士",
    "CN": "中国",
    "DE": "德国",
    "ES": "西班牙",
    "FR": "法国",
    "GB": "英国",
    "HK": "中国香港",
    "IN": "印度",
    "IT": "意大利",
    "JP": "日本",
    "KR": "韩国",
    "MO": "中国澳门",
    "NL": "荷兰",
    "NZ": "新西兰",
    "RU": "俄罗斯",
    "SE": "瑞典",
    "SG": "新加坡",
    "TW": "中国台湾",
    "US": "美国",
}


class PageViewInput(BaseModel):
    visitor_id: str = Field(..., min_length=8, max_length=128, description="匿名访客 ID")
    page_id: str = Field(default="unknown", max_length=64, description="页面 ID")
    page_label: str = Field(default="未知页面", max_length=80, description="页面中文名")
    path: str = Field(default="/", max_length=200, description="前端路由或虚拟路径")
    referrer: str = Field(default="", max_length=500, description="来源地址")
    language: str = Field(default="", max_length=50, description="浏览器语言")
    timezone: str = Field(default="", max_length=60, description="浏览器时区")


class XActivityInput(BaseModel):
    title: str = Field(..., min_length=2, max_length=120, description="活动标题")
    activity_type: str = Field(default="post", max_length=40, description="活动类型")
    event_date: str = Field(..., min_length=10, max_length=10, description="活动日期 YYYY-MM-DD")
    url: str = Field(default="", max_length=500, description="X 帖子或活动链接")
    note: str = Field(default="", max_length=500, description="备注")


class ConversionEventInput(BaseModel):
    visitor_id: str = Field(..., min_length=8, max_length=128, description="匿名访客 ID")
    event_type: str = Field(..., min_length=3, max_length=60, description="事件类型")
    event_label: str = Field(default="", max_length=120, description="事件标签")
    page_id: str = Field(default="unknown", max_length=64, description="页面 ID")
    page_label: str = Field(default="未知页面", max_length=80, description="页面中文名")


def _ensure_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(DB_PATH)) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS page_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visitor_id TEXT NOT NULL,
                page_id TEXT NOT NULL,
                page_label TEXT NOT NULL,
                path TEXT NOT NULL,
                referrer TEXT NOT NULL,
                referrer_host TEXT NOT NULL,
                country_code TEXT NOT NULL,
                country_name TEXT NOT NULL,
                language TEXT NOT NULL,
                timezone TEXT NOT NULL,
                ip_hash TEXT NOT NULL,
                visit_date TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_page_views_visit_date ON page_views(visit_date)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_page_views_country ON page_views(country_code)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_page_views_visitor ON page_views(visitor_id)"
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS x_activity_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                event_date TEXT NOT NULL,
                url TEXT NOT NULL,
                note TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_x_activity_events_event_date ON x_activity_events(event_date)"
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conversion_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visitor_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_label TEXT NOT NULL,
                page_id TEXT NOT NULL,
                page_label TEXT NOT NULL,
                country_code TEXT NOT NULL,
                country_name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_conversion_events_created_at ON conversion_events(created_at)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_conversion_events_event_type ON conversion_events(event_type)"
        )
        connection.commit()


def _get_connection() -> sqlite3.Connection:
    _ensure_db()
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _require_admin_token(x_admin_token: Optional[str]) -> None:
    if not PLATFORM_ADMIN_TOKEN:
        return
    if not x_admin_token or x_admin_token != PLATFORM_ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="访问分析后台口令无效。")


def _extract_client_ip(request: Request) -> Optional[str]:
    candidates: list[str] = []
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        candidates.extend([part.strip() for part in forwarded.split(",") if part.strip()])
    for header_name in ("x-real-ip", "x-client-ip"):
        header_value = request.headers.get(header_name, "").strip()
        if header_value:
            candidates.append(header_value)
    if request.client and request.client.host:
        candidates.append(request.client.host)

    for candidate in candidates:
        try:
            ip_value = ipaddress.ip_address(candidate)
        except ValueError:
            continue
        if (
            ip_value.is_private
            or ip_value.is_loopback
            or ip_value.is_reserved
            or ip_value.is_multicast
            or ip_value.is_link_local
            or ip_value.is_unspecified
        ):
            continue
        return candidate
    return None


def _hash_ip(ip_address_text: Optional[str]) -> str:
    if not ip_address_text:
        return "local-traffic"
    return hashlib.sha256(ip_address_text.encode("utf-8")).hexdigest()[:16]


def _extract_referrer_host(referrer: str) -> str:
    if not referrer:
        return "direct"
    try:
        parsed = urlparse(referrer)
    except ValueError:
        return "unknown"
    hostname = (parsed.netloc or "").lower()
    if hostname.startswith("www."):
        hostname = hostname[4:]
    return hostname or "unknown"


def _country_name_from_code(country_code: str) -> str:
    code = country_code.strip().upper()
    if not code:
        return "未知地区"
    return COUNTRY_DISPLAY_NAMES.get(code, code)


async def _resolve_country(request: Request) -> tuple[str, str]:
    for header_name in (
        "x-vercel-ip-country",
        "cf-ipcountry",
        "x-country-code",
        "x-appengine-country",
        "x-geo-country",
    ):
        country_code = request.headers.get(header_name, "").strip().upper()
        if country_code and country_code not in {"XX", "ZZ"}:
            return country_code, _country_name_from_code(country_code)

    client_ip = _extract_client_ip(request)
    if not client_ip:
        return "LOCAL", "本地 / 未识别"

    if client_ip in COUNTRY_CACHE:
        return COUNTRY_CACHE[client_ip]

    try:
        async with httpx.AsyncClient(timeout=2.5) as client:
            response = await client.get(f"https://ipapi.co/{client_ip}/json/")
        if response.is_success:
            payload = response.json()
            country_code = (payload.get("country_code") or "").strip().upper()
            country_name = (payload.get("country_name") or "").strip()
            if country_code:
                resolved = (country_code, country_name or _country_name_from_code(country_code))
                COUNTRY_CACHE[client_ip] = resolved
                return resolved
    except Exception:
        pass

    return "UN", "未知地区"


def _date_series(days: int) -> list[str]:
    today = datetime.now(SHANGHAI_TZ).date()
    start_day = today - timedelta(days=days - 1)
    return [
        (start_day + timedelta(days=offset)).isoformat()
        for offset in range(days)
    ]


def _since_date(days: int) -> str:
    return _date_series(days)[0]


def _safe_ratio(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return round((numerator / denominator) * 100, 1)


@router.post("/page-view")
async def record_page_view(payload: PageViewInput, request: Request):
    country_code, country_name = await _resolve_country(request)
    client_ip = _extract_client_ip(request)
    recorded_at = datetime.now(timezone.utc).isoformat()
    visit_date = datetime.now(SHANGHAI_TZ).date().isoformat()
    referrer_host = _extract_referrer_host(payload.referrer)

    with closing(_get_connection()) as connection:
        connection.execute(
            """
            INSERT INTO page_views (
                visitor_id,
                page_id,
                page_label,
                path,
                referrer,
                referrer_host,
                country_code,
                country_name,
                language,
                timezone,
                ip_hash,
                visit_date,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.visitor_id.strip(),
                payload.page_id.strip() or "unknown",
                payload.page_label.strip() or "未知页面",
                payload.path.strip() or "/",
                payload.referrer.strip(),
                referrer_host,
                country_code,
                country_name,
                payload.language.strip(),
                payload.timezone.strip(),
                _hash_ip(client_ip),
                visit_date,
                recorded_at,
            ),
        )
        connection.commit()

    return {
        "ok": True,
        "visit_date": visit_date,
        "country": {"code": country_code, "name": country_name},
    }


@router.post("/conversion-event")
async def record_conversion_event(payload: ConversionEventInput, request: Request):
    country_code, country_name = await _resolve_country(request)
    recorded_at = datetime.now(timezone.utc).isoformat()

    with closing(_get_connection()) as connection:
        connection.execute(
            """
            INSERT INTO conversion_events (
                visitor_id,
                event_type,
                event_label,
                page_id,
                page_label,
                country_code,
                country_name,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.visitor_id.strip(),
                payload.event_type.strip(),
                payload.event_label.strip(),
                payload.page_id.strip() or "unknown",
                payload.page_label.strip() or "未知页面",
                country_code,
                country_name,
                recorded_at,
            ),
        )
        connection.commit()

    return {"ok": True, "recorded_at": recorded_at}


@router.post("/x-activities")
async def create_x_activity(
    payload: XActivityInput,
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
):
    _require_admin_token(x_admin_token)
    try:
        datetime.strptime(payload.event_date, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="活动日期格式必须为 YYYY-MM-DD。") from exc

    created_at = datetime.now(timezone.utc).isoformat()
    with closing(_get_connection()) as connection:
        cursor = connection.execute(
            """
            INSERT INTO x_activity_events (
                title,
                activity_type,
                event_date,
                url,
                note,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payload.title.strip(),
                payload.activity_type.strip() or "post",
                payload.event_date.strip(),
                payload.url.strip(),
                payload.note.strip(),
                created_at,
            ),
        )
        connection.commit()

    return {
        "ok": True,
        "activity": {
            "id": cursor.lastrowid,
            "title": payload.title.strip(),
            "activity_type": payload.activity_type.strip() or "post",
            "event_date": payload.event_date.strip(),
            "url": payload.url.strip(),
            "note": payload.note.strip(),
            "created_at": created_at,
        },
    }


@router.get("/dashboard")
async def get_traffic_dashboard(
    days: int = Query(default=30, ge=7, le=180, description="统计天数"),
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
):
    _require_admin_token(x_admin_token)

    date_points = _date_series(days)
    today = date_points[-1]
    since_date = date_points[0]
    heatmap_since_date = _since_date(30)
    twitter_placeholders = ",".join(["?"] * len(TWITTER_REFERRER_HOSTS))
    lead_placeholders = ",".join(["?"] * len(LEAD_EVENT_TYPES))
    high_intent_placeholders = ",".join(["?"] * len(HIGH_INTENT_PAGE_IDS))

    with closing(_get_connection()) as connection:
        total_row = connection.execute(
            """
            SELECT
                COUNT(*) AS page_views,
                COUNT(DISTINCT visitor_id) AS unique_visitors,
                COUNT(DISTINCT country_code) AS country_count
            FROM page_views
            WHERE visit_date >= ?
            """,
            (since_date,),
        ).fetchone()

        today_row = connection.execute(
            """
            SELECT
                COUNT(*) AS page_views,
                COUNT(DISTINCT visitor_id) AS unique_visitors
            FROM page_views
            WHERE visit_date = ?
            """,
            (today,),
        ).fetchone()

        daily_rows = connection.execute(
            """
            SELECT
                visit_date,
                COUNT(*) AS page_views,
                COUNT(DISTINCT visitor_id) AS unique_visitors
            FROM page_views
            WHERE visit_date >= ?
            GROUP BY visit_date
            ORDER BY visit_date ASC
            """,
            (since_date,),
        ).fetchall()

        x_daily_rows = connection.execute(
            f"""
            SELECT
                visit_date,
                COUNT(*) AS page_views,
                COUNT(DISTINCT visitor_id) AS unique_visitors
            FROM page_views
            WHERE visit_date >= ?
              AND referrer_host IN ({twitter_placeholders})
            GROUP BY visit_date
            ORDER BY visit_date ASC
            """,
            (since_date, *TWITTER_REFERRER_HOSTS),
        ).fetchall()

        country_rows = connection.execute(
            """
            SELECT
                country_code,
                country_name,
                COUNT(*) AS page_views,
                COUNT(DISTINCT visitor_id) AS unique_visitors
            FROM page_views
            WHERE visit_date >= ?
            GROUP BY country_code, country_name
            ORDER BY page_views DESC, unique_visitors DESC
            """,
            (since_date,),
        ).fetchall()

        page_rows = connection.execute(
            """
            SELECT
                page_id,
                page_label,
                COUNT(*) AS page_views,
                COUNT(DISTINCT visitor_id) AS unique_visitors
            FROM page_views
            WHERE visit_date >= ?
            GROUP BY page_id, page_label
            ORDER BY page_views DESC, unique_visitors DESC
            LIMIT 8
            """,
            (since_date,),
        ).fetchall()

        referrer_rows = connection.execute(
            """
            SELECT
                referrer_host,
                COUNT(*) AS page_views,
                COUNT(DISTINCT visitor_id) AS unique_visitors
            FROM page_views
            WHERE visit_date >= ?
            GROUP BY referrer_host
            ORDER BY page_views DESC, unique_visitors DESC
            LIMIT 8
            """,
            (since_date,),
        ).fetchall()

        twitter_summary_row = connection.execute(
            f"""
            SELECT
                COUNT(*) AS page_views,
                COUNT(DISTINCT visitor_id) AS unique_visitors
            FROM page_views
            WHERE visit_date >= ?
              AND referrer_host IN ({twitter_placeholders})
            """,
            (since_date, *TWITTER_REFERRER_HOSTS),
        ).fetchone()

        twitter_host_rows = connection.execute(
            f"""
            SELECT
                referrer_host,
                COUNT(*) AS page_views,
                COUNT(DISTINCT visitor_id) AS unique_visitors
            FROM page_views
            WHERE visit_date >= ?
              AND referrer_host IN ({twitter_placeholders})
            GROUP BY referrer_host
            ORDER BY page_views DESC, unique_visitors DESC
            """,
            (since_date, *TWITTER_REFERRER_HOSTS),
        ).fetchall()

        twitter_landing_rows = connection.execute(
            f"""
            SELECT
                page_id,
                page_label,
                COUNT(*) AS page_views,
                COUNT(DISTINCT visitor_id) AS unique_visitors
            FROM page_views
            WHERE visit_date >= ?
              AND referrer_host IN ({twitter_placeholders})
            GROUP BY page_id, page_label
            ORDER BY page_views DESC, unique_visitors DESC
            LIMIT 5
            """,
            (since_date, *TWITTER_REFERRER_HOSTS),
        ).fetchall()

        heatmap_country_rows = connection.execute(
            """
            SELECT
                country_code,
                country_name,
                COUNT(*) AS page_views,
                COUNT(DISTINCT visitor_id) AS unique_visitors
            FROM page_views
            WHERE visit_date >= ?
            GROUP BY country_code, country_name
            ORDER BY page_views DESC, unique_visitors DESC
            LIMIT 60
            """,
            (heatmap_since_date,),
        ).fetchall()

        x_activity_rows = connection.execute(
            """
            SELECT
                id,
                title,
                activity_type,
                event_date,
                url,
                note,
                created_at
            FROM x_activity_events
            WHERE event_date >= ?
            ORDER BY event_date DESC, id DESC
            LIMIT 12
            """,
            (_since_date(max(days, 90)),),
        ).fetchall()

        funnel_country_rows = connection.execute(
            """
            SELECT
                country_code,
                country_name,
                COUNT(DISTINCT visitor_id) AS country_visitors
            FROM page_views
            WHERE visit_date >= ?
            GROUP BY country_code, country_name
            ORDER BY country_visitors DESC
            LIMIT 10
            """,
            (since_date,),
        ).fetchall()

        lead_event_country_rows = connection.execute(
            f"""
            SELECT
                country_code,
                COUNT(*) AS lead_events,
                COUNT(DISTINCT visitor_id) AS lead_visitors
            FROM conversion_events
            WHERE DATE(created_at) >= ?
              AND event_type IN ({lead_placeholders})
            GROUP BY country_code
            """,
            (since_date, *LEAD_EVENT_TYPES),
        ).fetchall()

    daily_map = {
        row["visit_date"]: {
            "date": row["visit_date"],
            "page_views": row["page_views"],
            "unique_visitors": row["unique_visitors"],
        }
        for row in daily_rows
    }
    daily = [
        daily_map.get(
            date_value,
            {"date": date_value, "page_views": 0, "unique_visitors": 0},
        )
        for date_value in date_points
    ]
    x_daily_map = {
        row["visit_date"]: {
            "date": row["visit_date"],
            "page_views": row["page_views"],
            "unique_visitors": row["unique_visitors"],
        }
        for row in x_daily_rows
    }
    x_daily = [
        x_daily_map.get(
            date_value,
            {"date": date_value, "page_views": 0, "unique_visitors": 0},
        )
        for date_value in date_points
    ]
    twitter_page_views = twitter_summary_row["page_views"] if twitter_summary_row else 0
    twitter_unique_visitors = twitter_summary_row["unique_visitors"] if twitter_summary_row else 0
    total_page_views = total_row["page_views"] if total_row else 0
    twitter_share_of_traffic = round((twitter_page_views / total_page_views) * 100, 1) if total_page_views else 0
    top_twitter_landing = twitter_landing_rows[0] if twitter_landing_rows else None
    lead_event_by_country = {
        row["country_code"]: {
            "lead_events": row["lead_events"],
            "lead_visitors": row["lead_visitors"],
        }
        for row in lead_event_country_rows
    }

    x_peak_correlation = []
    for row in x_activity_rows:
        event_date = row["event_date"]
        event_dt = datetime.strptime(event_date, "%Y-%m-%d").date()
        baseline_dates = [
            (event_dt - timedelta(days=offset)).isoformat()
            for offset in range(3, 0, -1)
        ]
        follow_dates = [
            (event_dt + timedelta(days=offset)).isoformat()
            for offset in range(0, 4)
        ]
        baseline_avg_x = round(
            sum(x_daily_map.get(date_value, {"page_views": 0})["page_views"] for date_value in baseline_dates) / 3,
            1,
        )
        follow_x_series = [
            x_daily_map.get(date_value, {"date": date_value, "page_views": 0, "unique_visitors": 0})
            for date_value in follow_dates
        ]
        follow_total_series = [
            daily_map.get(date_value, {"date": date_value, "page_views": 0, "unique_visitors": 0})
            for date_value in follow_dates
        ]
        peak_x_day = max(follow_x_series, key=lambda item: item["page_views"])
        peak_total_day = max(follow_total_series, key=lambda item: item["page_views"])
        x_peak_correlation.append(
            {
                "id": row["id"],
                "title": row["title"],
                "activity_type": row["activity_type"],
                "event_date": event_date,
                "url": row["url"],
                "note": row["note"],
                "baseline_x_avg": baseline_avg_x,
                "window_x_page_views": sum(item["page_views"] for item in follow_x_series),
                "window_total_page_views": sum(item["page_views"] for item in follow_total_series),
                "peak_x_date": peak_x_day["date"],
                "peak_x_page_views": peak_x_day["page_views"],
                "peak_total_date": peak_total_day["date"],
                "peak_total_page_views": peak_total_day["page_views"],
                "x_uplift": round(peak_x_day["page_views"] - baseline_avg_x, 1),
                "x_uplift_ratio": _safe_ratio(peak_x_day["page_views"] - baseline_avg_x, baseline_avg_x) if baseline_avg_x else (100.0 if peak_x_day["page_views"] > 0 else 0.0),
            }
        )

    funnel_countries = []
    with closing(_get_connection()) as connection:
        for row in funnel_country_rows:
            country_code = row["country_code"]
            intent_visitors_row = connection.execute(
                f"""
                SELECT COUNT(DISTINCT visitor_id) AS intent_visitors
                FROM page_views
                WHERE visit_date >= ?
                  AND country_code = ?
                  AND page_id IN ({high_intent_placeholders})
                """,
                (since_date, country_code, *HIGH_INTENT_PAGE_IDS.keys()),
            ).fetchone()
            proxy_leads_row = connection.execute(
                f"""
                SELECT COUNT(*) AS proxy_leads
                FROM (
                    SELECT visitor_id
                    FROM page_views
                    WHERE visit_date >= ?
                      AND country_code = ?
                      AND page_id IN ({high_intent_placeholders})
                    GROUP BY visitor_id
                    HAVING COUNT(DISTINCT page_id) >= 2 OR COUNT(*) >= 3
                ) AS proxy_pool
                """,
                (since_date, country_code, *HIGH_INTENT_PAGE_IDS.keys()),
            ).fetchone()
            top_pages_rows = connection.execute(
                f"""
                SELECT
                    page_id,
                    page_label,
                    COUNT(*) AS page_views,
                    COUNT(DISTINCT visitor_id) AS unique_visitors
                FROM page_views
                WHERE visit_date >= ?
                  AND country_code = ?
                  AND page_id IN ({high_intent_placeholders})
                GROUP BY page_id, page_label
                ORDER BY unique_visitors DESC, page_views DESC
                LIMIT 3
                """,
                (since_date, country_code, *HIGH_INTENT_PAGE_IDS.keys()),
            ).fetchall()
            actual_leads = lead_event_by_country.get(country_code, {}).get("lead_visitors", 0)
            proxy_leads = proxy_leads_row["proxy_leads"] if proxy_leads_row else 0
            country_visitors = row["country_visitors"]
            intent_visitors = intent_visitors_row["intent_visitors"] if intent_visitors_row else 0
            lead_signal_row = connection.execute(
                f"""
                SELECT COUNT(*) AS lead_signals
                FROM (
                    SELECT DISTINCT ce.visitor_id
                    FROM conversion_events ce
                    WHERE DATE(ce.created_at) >= ?
                      AND ce.country_code = ?
                      AND ce.event_type IN ({lead_placeholders})
                      AND EXISTS (
                          SELECT 1
                          FROM page_views pv
                          WHERE pv.visit_date >= ?
                            AND pv.country_code = ce.country_code
                            AND pv.visitor_id = ce.visitor_id
                            AND pv.page_id IN ({high_intent_placeholders})
                      )
                    UNION
                    SELECT visitor_id
                    FROM page_views
                    WHERE visit_date >= ?
                      AND country_code = ?
                      AND page_id IN ({high_intent_placeholders})
                    GROUP BY visitor_id
                    HAVING COUNT(DISTINCT page_id) >= 2 OR COUNT(*) >= 3
                ) AS lead_pool
                """,
                (
                    since_date,
                    country_code,
                    *LEAD_EVENT_TYPES,
                    since_date,
                    *HIGH_INTENT_PAGE_IDS.keys(),
                    since_date,
                    country_code,
                    *HIGH_INTENT_PAGE_IDS.keys(),
                ),
            ).fetchone()
            combined_leads = lead_signal_row["lead_signals"] if lead_signal_row else 0
            funnel_countries.append(
                {
                    "country_code": country_code,
                    "country_name": row["country_name"] or _country_name_from_code(country_code),
                    "country_visitors": country_visitors,
                    "intent_page_visitors": intent_visitors,
                    "lead_signals": combined_leads,
                    "actual_leads": actual_leads,
                    "proxy_leads": proxy_leads,
                    "page_conversion_rate": _safe_ratio(intent_visitors, country_visitors),
                    "lead_conversion_rate": _safe_ratio(combined_leads, intent_visitors),
                    "top_pages": [
                        {
                            "page_id": item["page_id"],
                            "page_label": item["page_label"],
                            "page_views": item["page_views"],
                            "unique_visitors": item["unique_visitors"],
                        }
                        for item in top_pages_rows
                    ],
                }
            )

    return {
        "ok": True,
        "meta": {
            "days": days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "admin_required": bool(PLATFORM_ADMIN_TOKEN),
            "switch_header": "X-Admin-Token",
        },
        "summary": {
            "today_page_views": today_row["page_views"] if today_row else 0,
            "today_unique_visitors": today_row["unique_visitors"] if today_row else 0,
            "range_page_views": total_page_views,
            "range_unique_visitors": total_row["unique_visitors"] if total_row else 0,
            "country_count": total_row["country_count"] if total_row else 0,
        },
        "daily": daily,
        "x_daily": x_daily,
        "countries": [
            {
                "country_code": row["country_code"],
                "country_name": row["country_name"] or _country_name_from_code(row["country_code"]),
                "page_views": row["page_views"],
                "unique_visitors": row["unique_visitors"],
            }
            for row in country_rows
        ],
        "pages": [
            {
                "page_id": row["page_id"],
                "page_label": row["page_label"],
                "page_views": row["page_views"],
                "unique_visitors": row["unique_visitors"],
            }
            for row in page_rows
        ],
        "referrers": [
            {
                "referrer_host": row["referrer_host"],
                "page_views": row["page_views"],
                "unique_visitors": row["unique_visitors"],
            }
            for row in referrer_rows
        ],
        "x_conversion": {
            "page_views": twitter_page_views,
            "unique_visitors": twitter_unique_visitors,
            "share_of_traffic": twitter_share_of_traffic,
            "top_landing_page": {
                "page_id": top_twitter_landing["page_id"],
                "page_label": top_twitter_landing["page_label"],
                "page_views": top_twitter_landing["page_views"],
                "unique_visitors": top_twitter_landing["unique_visitors"],
            } if top_twitter_landing else None,
            "hosts": [
                {
                    "referrer_host": row["referrer_host"],
                    "page_views": row["page_views"],
                    "unique_visitors": row["unique_visitors"],
                }
                for row in twitter_host_rows
            ],
            "landing_pages": [
                {
                    "page_id": row["page_id"],
                    "page_label": row["page_label"],
                    "page_views": row["page_views"],
                    "unique_visitors": row["unique_visitors"],
                }
                for row in twitter_landing_rows
            ],
        },
        "geo_heatmap_30d": {
            "days": 30,
            "countries": [
                {
                    "country_code": row["country_code"],
                    "country_name": row["country_name"] or _country_name_from_code(row["country_code"]),
                    "page_views": row["page_views"],
                    "unique_visitors": row["unique_visitors"],
                }
                for row in heatmap_country_rows
            ],
        },
        "x_activity_correlation": {
            "days": days,
            "events": x_peak_correlation,
        },
        "country_page_lead_funnel": {
            "days": days,
            "definition": {
                "intent_pages": list(HIGH_INTENT_PAGE_IDS.values()),
                "lead_signal_logic": "合作线索 = 真实线索事件 + 高意向代理信号；代理信号指同一访客在统计窗口内访问至少 2 个高意向页面或累计 3 次高意向访问。",
            },
            "countries": funnel_countries,
        },
    }
