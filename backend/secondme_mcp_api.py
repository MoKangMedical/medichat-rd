"""
SecondMe integration MCP adapter for MediChat-RD.

This exposes a minimal MCP-compatible JSON-RPC surface for SecondMe review:
- initialize
- ping
- tools/list
- tools/call
"""

from __future__ import annotations

from datetime import datetime
import json
import re
from typing import Any, Callable, Dict

from fastapi import APIRouter, HTTPException, Request

from knowledge_api import EXTENDED_DB
from rare_disease_agent import search_rare_disease_by_symptoms
from secondme_oauth import SecondMeOAuthClient, SecondMeOAuthError


router = APIRouter(prefix="/api/v1/secondme", tags=["SecondMe MCP"])
oauth_client = SecondMeOAuthClient()
JSONRPC_VERSION = "2.0"
MCP_PROTOCOL_VERSION = "2025-03-26"


def _jsonrpc_result(request_id: Any, result: Dict[str, Any]) -> Dict[str, Any]:
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}


def _jsonrpc_error(request_id: Any, code: int, message: str, *, data: Any = None) -> Dict[str, Any]:
    error = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "error": error}


def _extract_bearer_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "").strip()
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization bearer token")
    if not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Malformed Authorization header")
    token = auth_header[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty bearer token")
    return token


def _normalize_disease_entry(disease: Dict[str, Any]) -> Dict[str, Any]:
    hospitals = disease.get("specialist_hospitals") or []
    if isinstance(hospitals, str):
        hospitals = [item.strip() for item in hospitals.split("、") if item.strip()]
    return {
        "name": disease.get("name", ""),
        "name_en": disease.get("name_en", ""),
        "category": disease.get("category", "未分类"),
        "gene": disease.get("gene", "未知"),
        "inheritance": disease.get("inheritance"),
        "prevalence": disease.get("prevalence"),
        "treatment_summary": disease.get("treatment_summary"),
        "specialist_hospitals": hospitals,
    }


def _split_symptoms(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [
            part.strip()
            for part in re.split(r"[,\n，、；;]+", value)
            if part.strip()
        ]
    return []


async def _resolve_secondme_user(request: Request) -> Dict[str, Any]:
    token = _extract_bearer_token(request)
    try:
        user_raw = await oauth_client.fetch_user_info_raw(token)
    except SecondMeOAuthError as exc:
        raise HTTPException(status_code=401, detail=exc.message) from exc
    return {
        "display_name": user_raw.get("name") or user_raw.get("nickname") or user_raw.get("userName") or "SecondMe 用户",
        "user_id": user_raw.get("userId") or user_raw.get("id") or "",
    }


def _tool_search_diseases(arguments: Dict[str, Any], secondme_user: Dict[str, Any]) -> Dict[str, Any]:
    query = str(arguments.get("query", "")).strip()
    if not query:
        raise ValueError("query is required")
    limit = max(1, min(int(arguments.get("limit", 5)), 10))
    query_lower = query.lower()
    items = []
    for disease in EXTENDED_DB.values():
        haystacks = [
            disease.get("name", ""),
            disease.get("name_en", ""),
            disease.get("gene", ""),
            disease.get("category", ""),
            disease.get("symptoms", ""),
        ]
        if any(query_lower in str(item).lower() for item in haystacks if item):
            items.append(_normalize_disease_entry(disease))
        if len(items) >= limit:
            break
    return {
        "query": query,
        "total": len(items),
        "items": items,
        "resolved_user": secondme_user,
    }


def _tool_get_disease_detail(arguments: Dict[str, Any], secondme_user: Dict[str, Any]) -> Dict[str, Any]:
    disease_name = str(arguments.get("disease_name", "")).strip()
    if not disease_name:
        raise ValueError("disease_name is required")

    disease = EXTENDED_DB.get(disease_name)
    if disease is None:
        for item in EXTENDED_DB.values():
            name_cn = str(item.get("name", "")).strip().lower()
            name_en = str(item.get("name_en", "")).strip().lower()
            query = disease_name.lower()
            if (
                name_cn == query
                or name_en == query
                or query in name_cn
                or query in name_en
            ):
                disease = item
                break
    if disease is None:
        raise ValueError(f"未找到疾病：{disease_name}")

    detail = _normalize_disease_entry(disease)
    detail.update(
        {
            "icd10": disease.get("icd10"),
            "symptoms": disease.get("symptoms"),
            "diagnosis_criteria": disease.get("diagnosis_criteria"),
            "metadata": {
                "resolved_user": secondme_user,
                "timestamp": datetime.now().isoformat(),
            },
        }
    )
    return detail


def _tool_screen_symptoms(arguments: Dict[str, Any], secondme_user: Dict[str, Any]) -> Dict[str, Any]:
    symptoms = _split_symptoms(arguments.get("symptoms"))
    if not symptoms:
        raise ValueError("symptoms is required")

    matched_diseases = search_rare_disease_by_symptoms(symptoms)
    diagnoses = []
    for disease in matched_diseases[:5]:
        match_symptoms = []
        for symptom in symptoms:
            for key_symptom in disease.key_symptoms:
                if symptom in key_symptom or key_symptom in symptom:
                    match_symptoms.append(key_symptom)
                    break
        confidence = 0.0
        if disease.key_symptoms:
            confidence = round(len(match_symptoms) / len(disease.key_symptoms) * 100, 1)
        diagnoses.append(
            {
                "disease_name": disease.name_cn,
                "disease_name_en": disease.name_en,
                "confidence": confidence,
                "match_symptoms": match_symptoms,
                "omim_id": disease.omim_id,
                "gene": disease.gene,
                "diagnosis_method": disease.diagnosis_method,
                "treatment": disease.treatment,
            }
        )

    recommended_actions = [
        "建议前往罕见病诊疗中心就诊",
        "携带既往检查资料",
        "如有家族史请详细告知医生",
    ]
    if matched_diseases:
        recommended_actions.insert(0, f"建议进行{matched_diseases[0].diagnosis_method}")

    return {
        "input_symptoms": symptoms,
        "possible_diagnoses": diagnoses,
        "recommended_actions": recommended_actions,
        "resolved_user": secondme_user,
    }


ToolHandler = Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]

TOOL_DEFINITIONS: list[Dict[str, Any]] = [
    {
        "name": "medichat_search_diseases",
        "description": "Search the MediChat-RD rare-disease knowledge base by disease name, gene, category, or symptom keyword.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Disease keyword, symptom keyword, gene symbol, or category."},
                "limit": {"type": "integer", "description": "Maximum number of results to return.", "default": 5, "minimum": 1, "maximum": 10},
            },
            "required": ["query"],
        },
        "handler": _tool_search_diseases,
    },
    {
        "name": "medichat_get_disease_detail",
        "description": "Get structured detail for a rare disease, including gene, inheritance, diagnosis criteria, and treatment summary.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "disease_name": {"type": "string", "description": "Chinese or English disease name present in MediChat-RD."},
            },
            "required": ["disease_name"],
        },
        "handler": _tool_get_disease_detail,
    },
    {
        "name": "medichat_screen_symptoms",
        "description": "Screen a set of symptoms against the MediChat-RD rare-disease database and return ranked possible diagnoses.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symptoms": {
                    "description": "Either a symptom array or a comma-separated string.",
                    "oneOf": [
                        {"type": "array", "items": {"type": "string"}},
                        {"type": "string"},
                    ],
                },
            },
            "required": ["symptoms"],
        },
        "handler": _tool_screen_symptoms,
    },
]

TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {tool["name"]: tool for tool in TOOL_DEFINITIONS}


@router.get("/mcp/health")
async def secondme_mcp_health():
    return {
        "ok": True,
        "endpoint": "/api/v1/secondme/mcp",
        "tools": [tool["name"] for tool in TOOL_DEFINITIONS],
    }


@router.post("/mcp")
async def secondme_mcp_rpc(request: Request):
    payload = await request.json()
    request_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params") or {}

    if method == "initialize":
        return _jsonrpc_result(
            request_id,
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {
                    "name": "medichat-rd-secondme-mcp",
                    "version": "1.0.0",
                },
            },
        )

    if method == "ping":
        return _jsonrpc_result(request_id, {"ok": True})

    if method == "tools/list":
        tools = [
            {
                "name": tool["name"],
                "description": tool["description"],
                "inputSchema": tool["inputSchema"],
            }
            for tool in TOOL_DEFINITIONS
        ]
        return _jsonrpc_result(request_id, {"tools": tools})

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}
        tool = TOOL_REGISTRY.get(tool_name)
        if tool is None:
            return _jsonrpc_result(
                request_id,
                {
                    "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                    "isError": True,
                },
            )
        secondme_user = await _resolve_secondme_user(request)
        try:
            result = tool["handler"](arguments, secondme_user)
        except ValueError as exc:
            return _jsonrpc_result(
                request_id,
                {
                    "content": [{"type": "text", "text": str(exc)}],
                    "isError": True,
                },
            )
        return _jsonrpc_result(
            request_id,
            {
                "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}],
                "isError": False,
            },
        )

    return _jsonrpc_error(request_id, -32601, f"Unsupported method: {method}")
