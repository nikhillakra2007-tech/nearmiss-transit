"""Security helpers: CORS, validation notes, secret redaction."""
from __future__ import annotations

ALLOWED_ORIGINS = ["http://127.0.0.1:3000", "http://localhost:3000"]


def redact_secrets(data: dict) -> dict:
    out = dict(data)
    for key in list(out):
        if "key" in key.lower() or "secret" in key.lower() or "token" in key.lower():
            out[key] = "***"
    return out
