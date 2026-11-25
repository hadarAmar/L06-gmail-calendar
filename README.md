# gmail-calendar MCP Server

An MCP server built with Python, `uv`, and the official MCP Python SDK (`FastMCP`) over `stdio` transport. It exposes read-only and draft-only Gmail tools plus Google Calendar tools configured for the `Asia/Jerusalem` time zone.

## Prerequisites

1. Place your downloaded Google OAuth Desktop `client_secret*.json` file in `~/my-private`.
2. Authenticate once interactively to generate `~/my-private/token.json`:

```bash
uv run auth.py
```

The MCP server never opens a browser or copies credential files into the repository; it reads `token.json` directly from `GOOGLE_PRIVATE_DIR`.

## Running the MCP Server

Set `GOOGLE_PRIVATE_DIR` (defaults to `~/my-private` if unset) and start the server via `uv`:

```bash
GOOGLE_PRIVATE_DIR=~/my-private uv run gmail-calendar
```

You can also run it via:

```bash
GOOGLE_PRIVATE_DIR=~/my-private uv run server.py
```

### Example MCP Client Configuration

```json
{
  "mcpServers": {
    "gmail-calendar": {
      "command": "uv",
      "args": ["--directory", "/path/to/L06", "run", "gmail-calendar"],
      "env": {
        "GOOGLE_PRIVATE_DIR": "/path/to/my-private"
      }
    }
  }
}
```

## Available Tools

No tool sends emails or deletes emails/events.

1. `search_emails(query, max_results=10)` — Search Gmail messages and return metadata summaries.
2. `read_email(message_id)` — Read full headers and body of a Gmail message.
3. `create_draft(to, subject, body)` — Create a Gmail draft only (never sends).
4. `list_events(days_ahead=7)` — List upcoming primary calendar events in `Asia/Jerusalem`.
5. `find_free_slots(date, duration_minutes=30)` — Find free slots on `YYYY-MM-DD` between `08:00` and `20:00` (`Asia/Jerusalem`).
6. `create_event(title, start, end, description="")` — Create a calendar event in `Asia/Jerusalem` (accepts ISO-8601 timestamps).
