import copy
import unittest

from campusflow.exceptions import CampusFlowError, InvalidTransitionError, TicketNotFoundError, ValidationError
from campusflow.workflow import assign_ticket, get_ticket, reopen_ticket, update_status


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tickets = [{
            "id": "T001", "title": "Wi-Fi outage", "category": "Network",
            "urgency": "high", "affected_users": 15, "priority": "critical",
            "status": "open", "assigned_to": None,
        }]

    def assert_rejected_without_mutation(self, function, *args):
        before = copy.deepcopy(self.tickets)
        with self.assertRaises(CampusFlowError):
            function(self.tickets, *args)
        self.assertEqual(self.tickets, before)

    def test_assignment_normalizes_id_and_trims_name(self):
        result = assign_ticket(self.tickets, " t001 ", " Ada Okafor ")
        self.assertIs(result, self.tickets[0])
        self.assertEqual(result["assigned_to"], "Ada Okafor")

    def test_invalid_staff_names_do_not_mutate(self):
        for name in ("", "  ", None, 12):
            with self.subTest(name=name):
                self.assert_rejected_without_mutation(assign_ticket, "T001", name)

    def test_unknown_ids_rejected_by_all_operations(self):
        for function, args in (
            (get_ticket, ("T999",)), (assign_ticket, ("T999", "Ada")),
            (update_status, ("T999", "in_progress")), (reopen_ticket, ("T999",)),
        ):
            with self.subTest(function=function.__name__):
                self.assert_rejected_without_mutation(function, *args)

    def test_invalid_id_inputs(self):
        for ticket_id in (None, "", " ", 1):
            with self.subTest(ticket_id=ticket_id):
                self.assert_rejected_without_mutation(get_ticket, ticket_id)

    def test_unassigned_cannot_start(self):
        for assignee in (None, "", " "):
            self.tickets[0]["assigned_to"] = assignee
            with self.subTest(assignee=assignee):
                self.assert_rejected_without_mutation(update_status, "T001", "in_progress")

    def test_assigned_ticket_completes_lifecycle(self):
        assign_ticket(self.tickets, "T001", "Ada")
        result = update_status(self.tickets, "T001", " IN_PROGRESS ")
        self.assertIs(result, self.tickets[0])
        self.assertEqual(result["status"], "in_progress")
        self.assertEqual(update_status(self.tickets, "T001", "resolved")["status"], "resolved")

    def test_skipping_and_no_op_transitions_rejected(self):
        assign_ticket(self.tickets, "T001", "Ada")
        for status in ("resolved", "open"):
            self.assert_rejected_without_mutation(update_status, "T001", status)
        update_status(self.tickets, "T001", "in_progress")
        for status in ("open", "in_progress"):
            self.assert_rejected_without_mutation(update_status, "T001", status)

    def test_invalid_statuses_do_not_mutate(self):
        for status in ("closed", "", None, 1):
            with self.subTest(status=status):
                self.assert_rejected_without_mutation(update_status, "T001", status)

    def test_resolved_ticket_locked_until_explicit_reopen(self):
        self.tickets[0].update(status="resolved", assigned_to="Ada")
        self.assert_rejected_without_mutation(assign_ticket, "T001", "Bola")
        for status in ("open", "in_progress", "resolved"):
            self.assert_rejected_without_mutation(update_status, "T001", status)
        result = reopen_ticket(self.tickets, "T001")
        self.assertEqual(result["status"], "open")
        self.assertEqual(result["assigned_to"], "Ada")
        assign_ticket(self.tickets, "T001", "Bola")
        update_status(self.tickets, "T001", "in_progress")
        self.assertEqual(result["assigned_to"], "Bola")

    def test_only_resolved_tickets_can_reopen(self):
        for status in ("open", "in_progress"):
            self.tickets[0]["status"] = status
            self.assert_rejected_without_mutation(reopen_ticket, "T001")

    def test_reassignment_of_in_progress_ticket(self):
        self.tickets[0].update(status="in_progress", assigned_to="Ada")
        assign_ticket(self.tickets, "T001", "Bola")
        self.assertEqual(self.tickets[0]["assigned_to"], "Bola")
        self.assertEqual(self.tickets[0]["status"], "in_progress")

    def test_errors_match_shared_cli_exception_contract(self):
        before = copy.deepcopy(self.tickets)
        cases = (
            (TicketNotFoundError, assign_ticket, ('T999', 'Ada')),
            (ValidationError, assign_ticket, ('T001', ' ')),
            (ValidationError, update_status, ('T001', 'closed')),
            (InvalidTransitionError, update_status, ('T001', 'in_progress')),
        )
        for expected, operation, args in cases:
            with self.subTest(operation=operation.__name__, args=args):
                with self.assertRaises(expected) as caught:
                    operation(self.tickets, *args)
                self.assertIsInstance(caught.exception, CampusFlowError)
                self.assertEqual(self.tickets, before)
