"""
Standalone FastAPI app for the SecondMe MCP integration endpoint.

This keeps the integration runtime independent from the heavier main.py stack.
"""

from fastapi import FastAPI

from secondme_mcp_api import router as secondme_mcp_router


app = FastAPI(
    title="MediChat-RD SecondMe MCP",
    description="Standalone MCP adapter for the MediChat-RD SecondMe integration.",
    version="1.0.0",
)

app.include_router(secondme_mcp_router)


@app.get("/")
async def root():
    return {
        "ok": True,
        "name": "medichat-rd-secondme-mcp",
        "mcp_endpoint": "/api/v1/secondme/mcp",
    }
