"""Assignment and lifecycle operations on a shared list of ticket dictionaries."""


from campusflow.exceptions import InvalidTransitionError, TicketNotFoundError, ValidationError
from campusflow.validation import can_transition, validate_staff_name, validate_transition

def get_ticket(tickets, ticket_id):
    """Return the matching ticket; raise TicketNotFoundError for an unknown ID."""
    if not isinstance(ticket_id, str) or not ticket_id.strip():
        raise TicketNotFoundError("Ticket ID must be a non-empty string.")
    normalized_id = ticket_id.strip().upper()
    for ticket in tickets:
        if ticket["id"] == normalized_id:
            return ticket
    raise TicketNotFoundError(f"Unknown ticket ID: {normalized_id}")


def assign_ticket(tickets, ticket_id, staff_name):
    """Assign or reassign an unresolved ticket and return the updated record."""
    ticket = get_ticket(tickets, ticket_id)
    if ticket["status"] == "resolved":
        raise InvalidTransitionError("Reopen a resolved ticket before assigning it.")
    ticket["assigned_to"] = validate_staff_name(staff_name)
    return ticket


def update_status(tickets, ticket_id, new_status):
    """Advance open → in_progress → resolved; reopening is a separate operation."""
    ticket = get_ticket(tickets, ticket_id)
    ticket["status"] = validate_transition(ticket, new_status)
    return ticket


def reopen_ticket(tickets, ticket_id):
    """Explicitly reopen a resolved ticket, preserving its assignment."""
    ticket = get_ticket(tickets, ticket_id)
    if ticket["status"] != "resolved":
        raise InvalidTransitionError("Only a resolved ticket can be reopened.")
    ticket["status"] = "open"
    return ticket
