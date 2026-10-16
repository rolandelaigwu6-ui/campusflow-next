"""Ticket creation, validation, priority engine, and lookup for CampusFlow."""

from typing import Any, Dict, List, Optional
from campusflow.exceptions import TicketNotFoundError, ValidationError

from campusflow.validation import (
    ALLOWED_CATEGORIES, ALLOWED_URGENCIES, validate_title,
    validate_category, validate_urgency, validate_affected_users,
)


def validate_ticket_input(
    title: Any, category: Any, urgency: Any, affected_users: Any
) -> Dict[str, Any]:
    """Validate domain inputs before mutation; affected_users must be an integer."""
    return {
        "title": validate_title(title),
        "category": validate_category(category),
        "urgency": validate_urgency(urgency),
        "affected_users": validate_affected_users(affected_users),
    }


def calculate_priority(urgency: str, affected_users: int) -> str:
    """Calculate priority according to the four strict rules in order.

    Rule 1: high urgency AND 10 or more affected users -> critical
    Rule 2: high urgency OR 10 or more affected users  -> high
    Rule 3: medium urgency OR 3 or more affected users -> medium
    Rule 4: all remaining valid tickets                -> low
    """
    norm_urgency = urgency.strip().lower() if isinstance(urgency, str) else ""

    # Rule 1
    if norm_urgency == "high" and affected_users >= 10:
        return "critical"
    # Rule 2
    if norm_urgency == "high" or affected_users >= 10:
        return "high"
    # Rule 3
    if norm_urgency == "medium" or affected_users >= 3:
        return "medium"
    # Rule 4
    return "low"


def generate_next_id(tickets: List[Dict[str, Any]]) -> str:
    """Generate the next sequential ticket ID (T001, T002, ...).

    Scans existing IDs to avoid collisions even after reload or deletions.
    """
    max_num = 0
    for ticket in tickets:
        tid = str(ticket.get("id", "")).strip().upper()
        if tid.startswith("T") and tid[1:].isdigit():
            max_num = max(max_num, int(tid[1:]))
    return f"T{max_num + 1:03d}"


def create_ticket(
    tickets: List[Dict[str, Any]],
    title: Any,
    category: Any,
    urgency: Any,
    affected_users: Any,
) -> Dict[str, Any]:
    """Validate data, calculate priority, assign unique ID, and store ticket.

    Args:
        tickets: The list of tickets to append to.
        title: Title of the problem.
        category: Network, Hardware, Software, or Other.
        urgency: low, medium, or high.
        affected_users: Positive integer count.

    Returns:
        The newly created ticket dictionary.
    """
    validated = validate_ticket_input(title, category, urgency, affected_users)
    priority = calculate_priority(validated["urgency"], validated["affected_users"])
    ticket_id = generate_next_id(tickets)

    ticket: Dict[str, Any] = {
        "id": ticket_id,
        "title": validated["title"],
        "category": validated["category"],
        "urgency": validated["urgency"],
        "affected_users": validated["affected_users"],
        "priority": priority,
        "status": "open",
        "assigned_to": None,
        "notes": [],
    }

    tickets.append(ticket)
    return ticket


def get_ticket(tickets: List[Dict[str, Any]], ticket_id: str) -> Dict[str, Any]:
    """Look up a ticket by ID.

    Raises:
        TicketNotFoundError: If ticket_id does not exist.
    """
    if not isinstance(ticket_id, str):
        raise TicketNotFoundError(f"Invalid ticket ID: {ticket_id}")

    normalized_id = ticket_id.strip().upper()
    for ticket in tickets:
        if str(ticket.get("id", "")).strip().upper() == normalized_id:
            return ticket
    raise TicketNotFoundError(f"Ticket with ID '{ticket_id}' not found.")


def list_tickets(tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return a list of all tickets."""
    return list(tickets)
