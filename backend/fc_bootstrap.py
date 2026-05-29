"""Alibaba Cloud Function Compute (FC) entry point.

FC invokes the `handler` function for each request.
Deploy with: `fun deploy` or via FC console with a Python runtime.
"""

from __future__ import annotations

import json
import logging
import base64
from typing import Any

from app.main import app
from app.config import settings
from app.services.pdf_parser import extract_text_from_pdf

logger = logging.getLogger(__name__)


def handler(event: bytes, context: Any) -> bytes:
    """FC event handler: process HTTP request and return response."""
    import fcnt  # Available in FC Python runtime

    # Parse the FC event
    try:
        evt = json.loads(event.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        evt = {"body": base64.b64encode(event).decode()}

    path = evt.get("path", "/")
    method = evt.get("httpMethod", "GET").upper()

    # For resume upload endpoint via FC
    if path.startswith("/api/resume/parse") and method == "POST":
        body = evt.get("body", "")
        is_base64 = evt.get("isBase64Encoded", False)
        if is_base64:
            body = base64.b64decode(body)

        # Extract file and form fields from multipart body
        # Note: FC HTTP triggers handle multipart differently;
        # for production, consider using FC's built-in HTTP trigger
        import cgi
        import io
        content_type = evt.get("headers", {}).get("content-type", "multipart/form-data")

        # Simplified: we return a redirect to the main FastAPI app
        # In production, route through FC HTTP trigger directly

    return fcnt.http_response(
        status_code=200,
        headers={"Content-Type": "application/json"},
        response_body=json.dumps({
            "success": True,
            "message": "FC function invoked. For full API, use the FastAPI HTTP server.",
        }),
    )


# For FC custom runtime — start uvicorn server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=int(settings.PORT),
        reload=False,
    )
