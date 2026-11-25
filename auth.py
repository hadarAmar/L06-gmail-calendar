"""Authenticate with Google OAuth and store token.json in ~/my-private."""

from pathlib import Path
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
]

PRIVATE_DIR = Path.home() / "my-private"
TOKEN_PATH = PRIVATE_DIR / "token.json"


def find_client_secret(private_dir: Path) -> Path:
    """Return the single client_secret*.json file in private_dir."""
    matches = sorted(private_dir.glob("client_secret*.json"))
    if not matches:
        raise FileNotFoundError(
            f"No client_secret*.json file found in {private_dir}"
        )
    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple client_secret*.json files found in {private_dir}; "
            "keep only the intended file."
        )
    return matches[0]


def save_token(creds: Credentials, token_path: Path) -> None:
    """Write credentials JSON to token_path with owner-only permissions."""
    token_path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(token_path.parent, 0o700)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    os.chmod(token_path, 0o600)


def authenticate() -> Credentials:
    """Load, refresh, or interactively obtain Google OAuth credentials."""
    creds: Credentials | None = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_token(creds, TOKEN_PATH)
        return creds

    client_secret_path = find_client_secret(PRIVATE_DIR)
    print(f"Using client secrets file: {client_secret_path.name}")
    print("Opening browser for Google OAuth consent...")
    flow = InstalledAppFlow.from_client_secrets_file(
        str(client_secret_path), SCOPES
    )
    creds = flow.run_local_server(port=0)
    save_token(creds, TOKEN_PATH)
    return creds


def main() -> None:
    """Run OAuth authentication and report status without exposing secrets."""
    creds = authenticate()
    print(f"Authentication successful: valid={creds.valid}")
    print(f"Saved credentials to: {TOKEN_PATH}")


if __name__ == "__main__":
    main()
