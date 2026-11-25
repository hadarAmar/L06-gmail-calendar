"""Google OAuth credential loading and API service builders."""

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
]
TIMEZONE = "Asia/Jerusalem"


def get_private_dir() -> Path:
    """Resolve GOOGLE_PRIVATE_DIR (defaulting to ~/my-private if unset)."""
    raw = os.environ.get("GOOGLE_PRIVATE_DIR")
    private_dir = Path(raw).expanduser() if raw else Path.home() / "my-private"
    if not private_dir.is_dir():
        raise FileNotFoundError(
            f"GOOGLE_PRIVATE_DIR does not exist: {private_dir}"
        )
    return private_dir


def get_credentials() -> Credentials:
    """Load token.json from GOOGLE_PRIVATE_DIR and refresh without a browser."""
    private_dir = get_private_dir()
    token_path = private_dir / "token.json"
    if not token_path.exists():
        raise FileNotFoundError(
            f"Missing token.json in {private_dir}. Run auth.py first."
        )

    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds.valid:
        return creds

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json(), encoding="utf-8")
        os.chmod(token_path, 0o600)
        return creds

    raise RuntimeError(
        "Google credentials are invalid and cannot be refreshed automatically. "
        "Run auth.py interactively to re-authenticate."
    )


def build_gmail_service() -> Resource:
    """Build an authenticated Gmail API v1 client."""
    return build("gmail", "v1", credentials=get_credentials(), cache_discovery=False)


def build_calendar_service() -> Resource:
    """Build an authenticated Google Calendar API v3 client."""
    return build(
        "calendar", "v3", credentials=get_credentials(), cache_discovery=False
    )
