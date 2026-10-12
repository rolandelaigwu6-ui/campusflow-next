"""Read-only queue and reporting functions."""

PRIORITIES = ("critical", "high", "medium", "low")
STATUSES = ("open", "in_progress", "resolved")


def get_work_queue(tickets):
    """Return open tickets by priority, then numeric ID, without changing storage."""
    priority_rank = {priority: rank for rank, priority in enumerate(PRIORITIES)}
    return sorted(
        (ticket for ticket in tickets if ticket["status"] == "open"),
        key=lambda ticket: (priority_rank[ticket["priority"]], int(ticket["id"][1:])),
    )


def generate_report(tickets):
    """Count all tickets, including zero counts for each supported status/priority."""
    report = {
        "total": 0,
        "by_status": dict.fromkeys(STATUSES, 0),
        "by_priority": dict.fromkeys(PRIORITIES, 0),
    }
    for ticket in tickets:
        report["by_status"][ticket["status"]] += 1
        report["by_priority"][ticket["priority"]] += 1
        report["total"] += 1
    return report
