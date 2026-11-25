"""FastMCP stdio server exposing read/draft Gmail and Calendar tools."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from l06 import calendar_tools, gmail_tools

mcp = FastMCP("gmail-calendar")


@mcp.tool(description="Search Gmail messages by query and return message summaries.")
def search_emails(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Search Gmail messages matching a Gmail search query."""
    return gmail_tools.search_emails(query=query, max_results=max_results)


@mcp.tool(description="Read the headers and body of a Gmail message by its ID.")
def read_email(message_id: str) -> dict[str, Any]:
    """Read a full Gmail message by message ID."""
    return gmail_tools.read_email(message_id=message_id)


@mcp.tool(description="Create a Gmail draft email only (never sends the message).")
def create_draft(to: str, subject: str, body: str) -> dict[str, Any]:
    """Create a Gmail draft without sending it."""
    return gmail_tools.create_draft(to=to, subject=subject, body=body)


@mcp.tool(description="List upcoming Google Calendar events in Asia/Jerusalem time.")
def list_events(days_ahead: int = 7) -> list[dict[str, Any]]:
    """List primary calendar events for the upcoming days_ahead days."""
    return calendar_tools.list_events(days_ahead=days_ahead)


@mcp.tool(
    description=(
        "Find available time slots on a YYYY-MM-DD date (08:00-20:00 Asia/Jerusalem)."
    )
)
def find_free_slots(date: str, duration_minutes: int = 30) -> list[dict[str, Any]]:
    """Find free intervals of at least duration_minutes on the given date."""
    return calendar_tools.find_free_slots(
        date=date, duration_minutes=duration_minutes
    )


@mcp.tool(description="Create a Google Calendar event in Asia/Jerusalem time.")
def create_event(
    title: str, start: str, end: str, description: str = ""
) -> dict[str, Any]:
    """Create an event on the primary Google Calendar."""
    return calendar_tools.create_event(
        title=title, start=start, end=end, description=description
    )


def main() -> None:
    """Run the gmail-calendar MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
