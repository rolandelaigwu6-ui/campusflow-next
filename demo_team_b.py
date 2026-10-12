"""Run a deterministic Team B demonstration: python3 demo_team_b.py."""

from pprint import pprint

from campusflow.reports import generate_report, get_work_queue
from campusflow.workflow import assign_ticket, reopen_ticket, update_status


def main():
    tickets = [
        {"id": "T001", "title": "Mouse replacement", "category": "Hardware",
         "urgency": "low", "affected_users": 1, "priority": "low",
         "status": "open", "assigned_to": None},
        {"id": "T002", "title": "Campus Wi-Fi outage", "category": "Network",
         "urgency": "high", "affected_users": 15, "priority": "critical",
         "status": "open", "assigned_to": None},
    ]
    print("Open queue (critical first):")
    pprint(get_work_queue(tickets))
    try:
        update_status(tickets, "T002", "in_progress")
    except ValueError as error:
        print(f"Expected rejection: {error}")
    assign_ticket(tickets, "T002", "Ada")
    update_status(tickets, "T002", "in_progress")
    update_status(tickets, "T002", "resolved")
    print("Report after resolving T002:")
    pprint(generate_report(tickets))
    try:
        assign_ticket(tickets, "T002", "Bola")
    except ValueError as error:
        print(f"Expected rejection: {error}")
    reopen_ticket(tickets, "T002")
    assign_ticket(tickets, "T002", "Bola")
    print("Explicitly reopened and reassigned ticket:")
    pprint(tickets[1])


if __name__ == "__main__":
    main()
