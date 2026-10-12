"""Unit tests for CampusFlow ticket creation, validation, and priority calculation."""

import unittest
from campusflow.exceptions import TicketNotFoundError, ValidationError
from campusflow.tickets import (
    calculate_priority,
    create_ticket,
    generate_next_id,
    get_ticket,
    list_tickets,
    validate_ticket_input,
)


class TestTicketPriorityEngine(unittest.TestCase):
    """Test priority calculation engine according to Rules 1–4."""

    def test_rule1_high_urgency_and_10_or_more_users_critical(self):
        # High urgency + 12 affected users -> critical (Required Acceptance)
        self.assertEqual(calculate_priority("high", 12), "critical")
        # Boundary: High urgency + exactly 10 affected users -> critical
        self.assertEqual(calculate_priority("high", 10), "critical")

    def test_rule2_high_urgency_or_10_or_more_users_high(self):
        # High urgency + 2 affected users -> high (Required Acceptance)
        self.assertEqual(calculate_priority("high", 2), "high")
        # High urgency + 9 affected users -> high
        self.assertEqual(calculate_priority("high", 9), "high")
        # Medium urgency + 10 users -> high (triggers Rule 2 via users >= 10)
        self.assertEqual(calculate_priority("medium", 10), "high")
        # Low urgency + 15 users -> high (triggers Rule 2 via users >= 10)
        self.assertEqual(calculate_priority("low", 15), "high")

    def test_rule3_medium_urgency_or_3_or_more_users_medium(self):
        # Low urgency + 4 affected users -> medium (Required Acceptance)
        self.assertEqual(calculate_priority("low", 4), "medium")
        # Low urgency + exactly 3 affected users -> medium
        self.assertEqual(calculate_priority("low", 3), "medium")
        # Medium urgency + 1 affected user -> medium (triggers Rule 3 via urgency)
        self.assertEqual(calculate_priority("medium", 1), "medium")
        # Medium urgency + 2 affected users -> medium
        self.assertEqual(calculate_priority("medium", 2), "medium")

    def test_rule4_all_remaining_valid_tickets_low(self):
        # Low urgency + 1 affected user -> low (Required Acceptance)
        self.assertEqual(calculate_priority("low", 1), "low")
        # Low urgency + 2 affected users -> low
        self.assertEqual(calculate_priority("low", 2), "low")


class TestTicketValidation(unittest.TestCase):
    """Test validation of inputs and normalization."""

    def test_reject_zero_affected_users(self):
        # Zero affected users -> rejected (Required Acceptance)
        with self.assertRaises(ValidationError):
            validate_ticket_input("Wi-Fi issue", "Network", "high", 0)

    def test_reject_negative_affected_users(self):
        with self.assertRaises(ValidationError):
            validate_ticket_input("Wi-Fi issue", "Network", "high", -5)

    def test_reject_decimal_affected_users(self):
        with self.assertRaises(ValidationError):
            validate_ticket_input("Wi-Fi issue", "Network", "high", 3.5)

    def test_reject_non_numeric_affected_users(self):
        with self.assertRaises(ValidationError):
            validate_ticket_input("Wi-Fi issue", "Network", "high", "many")

    def test_reject_boolean_affected_users(self):
        with self.assertRaises(ValidationError):
            validate_ticket_input("Wi-Fi issue", "Network", "high", True)

    def test_reject_blank_or_whitespace_title(self):
        with self.assertRaises(ValidationError):
            validate_ticket_input("", "Network", "high", 5)
        with self.assertRaises(ValidationError):
            validate_ticket_input("   ", "Network", "high", 5)

    def test_reject_invalid_category(self):
        with self.assertRaises(ValidationError):
            validate_ticket_input("Printer jam", "Printers", "low", 1)

    def test_reject_invalid_urgency(self):
        with self.assertRaises(ValidationError):
            validate_ticket_input("Printer jam", "Hardware", "immediate", 1)

    def test_normalize_valid_inputs(self):
        validated = validate_ticket_input(
            "  Server lag  ", "network", "HIGH", "15"
        )
        self.assertEqual(validated["title"], "Server lag")
        self.assertEqual(validated["category"], "Network")
        self.assertEqual(validated["urgency"], "high")
        self.assertEqual(validated["affected_users"], 15)


class TestTicketCreationAndLookup(unittest.TestCase):
    """Test ticket creation, unique ID sequencing, and lookup."""

    def setUp(self):
        self.tickets = []

    def test_create_ticket_populates_all_required_fields(self):
        ticket = create_ticket(
            self.tickets,
            title="Campus Wi-Fi is down",
            category="Network",
            urgency="high",
            affected_users=15,
        )

        self.assertEqual(ticket["id"], "T001")
        self.assertEqual(ticket["title"], "Campus Wi-Fi is down")
        self.assertEqual(ticket["category"], "Network")
        self.assertEqual(ticket["urgency"], "high")
        self.assertEqual(ticket["affected_users"], 15)
        self.assertEqual(ticket["priority"], "critical")
        self.assertEqual(ticket["status"], "open")
        self.assertIsNone(ticket["assigned_to"])
        self.assertEqual(len(self.tickets), 1)

    def test_sequential_ticket_id_generation(self):
        t1 = create_ticket(self.tickets, "Bug A", "Software", "low", 1)
        t2 = create_ticket(self.tickets, "Bug B", "Hardware", "medium", 2)
        t3 = create_ticket(self.tickets, "Bug C", "Other", "high", 10)

        self.assertEqual(t1["id"], "T001")
        self.assertEqual(t2["id"], "T002")
        self.assertEqual(t3["id"], "T003")

    def test_id_generation_with_existing_gaps(self):
        existing = [{"id": "T001"}, {"id": "T009"}]
        next_id = generate_next_id(existing)
        self.assertEqual(next_id, "T010")

    def test_get_ticket_success_and_case_insensitivity(self):
        created = create_ticket(self.tickets, "Lab PC", "Hardware", "low", 1)
        retrieved = get_ticket(self.tickets, "t001")
        self.assertEqual(retrieved["id"], created["id"])

    def test_get_ticket_raises_not_found(self):
        with self.assertRaises(TicketNotFoundError):
            get_ticket(self.tickets, "T999")

    def test_list_tickets_returns_all(self):
        create_ticket(self.tickets, "Task 1", "Software", "low", 1)
        create_ticket(self.tickets, "Task 2", "Software", "medium", 3)
        all_tickets = list_tickets(self.tickets)
        self.assertEqual(len(all_tickets), 2)


if __name__ == "__main__":
    unittest.main()
