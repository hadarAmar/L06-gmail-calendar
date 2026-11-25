"""Read-only Gmail search/read and draft-only composition helpers."""

import base64
from email.message import EmailMessage
from typing import Any

from l06.google_client import build_gmail_service


def _headers_map(payload: dict[str, Any]) -> dict[str, str]:
    """Extract lowercase-keyed header values from a Gmail message payload."""
    headers = payload.get("headers", [])
    return {
        h["name"].lower(): h.get("value", "")
        for h in headers
        if "name" in h
    }


def _decode_b64(data: str) -> str:
    """Decode Gmail base64url-encoded body data."""
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii")).decode(
        "utf-8", errors="replace"
    )


def _extract_body(payload: dict[str, Any]) -> str:
    """Extract plain text (falling back to HTML) from a MIME payload tree."""
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")
    if body_data and mime_type == "text/plain":
        return _decode_b64(body_data)

    parts = payload.get("parts", [])
    html_fallback = ""
    for part in parts:
        text = _extract_body(part)
        if not text:
            continue
        if part.get("mimeType") == "text/plain" or part.get("parts"):
            return text
        if not html_fallback:
            html_fallback = text

    if html_fallback:
        return html_fallback
    if body_data:
        return _decode_b64(body_data)
    return ""


def search_emails(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Search Gmail messages matching query and return metadata summaries."""
    limit = max(1, min(max_results, 50))
    service = build_gmail_service()
    resp = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=limit)
        .execute()
    )
    items = resp.get("messages", [])
    results: list[dict[str, Any]] = []
    for item in items:
        msg = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=item["id"],
                format="metadata",
                metadataHeaders=["Subject", "From", "Date"],
            )
            .execute()
        )
        headers = _headers_map(msg.get("payload", {}))
        results.append(
            {
                "id": msg["id"],
                "thread_id": msg.get("threadId", ""),
                "subject": headers.get("subject", ""),
                "from": headers.get("from", ""),
                "date": headers.get("date", ""),
                "snippet": msg.get("snippet", ""),
            }
        )
    return results


def read_email(message_id: str) -> dict[str, Any]:
    """Read full headers and decoded body of a Gmail message by ID."""
    service = build_gmail_service()
    msg = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )
    payload = msg.get("payload", {})
    headers = _headers_map(payload)
    return {
        "id": msg["id"],
        "thread_id": msg.get("threadId", ""),
        "subject": headers.get("subject", ""),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "date": headers.get("date", ""),
        "snippet": msg.get("snippet", ""),
        "body": _extract_body(payload),
    }


def create_draft(to: str, subject: str, body: str) -> dict[str, Any]:
    """Create a Gmail draft message without sending it."""
    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    service = build_gmail_service()
    draft = (
        service.users()
        .drafts()
        .create(userId="me", body={"message": {"raw": raw}})
        .execute()
    )
    return {
        "draft_id": draft["id"],
        "message_id": draft.get("message", {}).get("id", ""),
        "to": to,
        "subject": subject,
        "status": "draft_created",
    }
