"""Engineer A reliability checks through public application APIs.

AI-assisted implementation evidence; personal authorship and understanding must
be demonstrated separately by the engineers.
"""
import copy
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from campusflow.exceptions import StorageError, ValidationError
from campusflow.notes import add_note
from campusflow.reports import generate_report
from campusflow.storage import load_tickets, save_tickets
from campusflow.tickets import create_ticket
from campusflow.workflow import assign_ticket, update_status, reopen_ticket
from main import handle_create_ticket


class ReliabilityRegressions(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'tickets.json'
        self.tickets = []
        self.ticket = create_ticket(self.tickets, 'Router problem', 'Network', 'high', 10)

    def assert_rejected_load(self, incoming):
        self.path.write_text(json.dumps(incoming), encoding='utf-8')
        source = self.path.read_bytes()
        before = copy.deepcopy(self.tickets)
        with self.assertRaises(StorageError):
            # Match the caller's replace-on-success contract.
            self.tickets = load_tickets(self.path)
        self.assertEqual(self.tickets, before)
        self.assertEqual(self.path.read_bytes(), source)

    def test_create_rejects_invalid_counts_without_consuming_id(self):
        for value in ('10', ' 2 ', 0, -1, 1.0, True, False, None):
            with self.subTest(value=value):
                before = copy.deepcopy(self.tickets)
                with self.assertRaises(ValidationError):
                    create_ticket(self.tickets, 'Invalid', 'Network', 'low', value)
                self.assertEqual(self.tickets, before)
        self.assertEqual(create_ticket(self.tickets, 'Next ticket', 'Other', 'low', 1)['id'], 'T002')

    def test_invalid_create_fields_preserve_collection(self):
        for title, category, urgency in [('', 'Network', 'low'), ('Valid', 'Invalid', 'low'), ('Valid', 'Network', 'urgent')]:
            before = copy.deepcopy(self.tickets)
            with self.assertRaises(ValidationError):
                create_ticket(self.tickets, title, category, urgency, 1)
            self.assertEqual(self.tickets, before)

    def test_null_notes_rejected_on_load_and_save(self):
        self.ticket['notes'] = None
        self.assert_rejected_load(self.tickets)
        self.path.write_text('original contents', encoding='utf-8')
        with self.assertRaises(StorageError):
            save_tickets(self.tickets, self.path)
        self.assertEqual(self.path.read_text(), 'original contents')

    def test_wrong_enum_types_reject_entire_batch(self):
        for field in ('status', 'priority', 'category', 'urgency'):
            for value in ([], {}, True, None):
                with self.subTest(field=field, value=value):
                    invalid = copy.deepcopy(self.ticket)
                    invalid['id'] = 'T002'
                    invalid[field] = value
                    self.assert_rejected_load([self.ticket, invalid])

    def test_invalid_ticket_ids_rejected(self):
        for value in ('t001', ' T001 ', 'T²', 'T000', 'T-001', 'T', None):
            with self.subTest(value=value):
                invalid = copy.deepcopy(self.ticket)
                invalid['id'] = value
                self.assert_rejected_load([invalid])

    def test_case_equivalent_ticket_duplicates_rejected(self):
        invalid = copy.deepcopy(self.ticket)
        invalid['id'] = 't001'
        self.assert_rejected_load([self.ticket, invalid])

    def test_invalid_note_shapes_and_duplicates_rejected(self):
        valid = {'note_id': 'N001', 'author': 'Operator', 'message': 'Router checked'}
        bad_notes = [None, {}, 'text', {'note_id': 'N001'},
                     {**valid, 'author': ' '}, {**valid, 'message': 'tiny'},
                     {**valid, 'message': 'x' * 301}]
        for note in bad_notes:
            with self.subTest(note=note):
                invalid = copy.deepcopy(self.ticket)
                invalid['notes'] = [note]
                self.assert_rejected_load([invalid])
        invalid = copy.deepcopy(self.ticket)
        invalid['notes'] = [valid, copy.deepcopy(valid)]
        self.assert_rejected_load([invalid])

    def test_invalid_note_ids_rejected(self):
        for value in ('n001', ' N001 ', 'N²', 'N000', None):
            with self.subTest(value=value):
                invalid = copy.deepcopy(self.ticket)
                invalid['notes'] = [{'note_id': value, 'author': 'Operator', 'message': 'Router checked'}]
                self.assert_rejected_load([invalid])

    def test_non_utf8_file_rejected_without_state_loss(self):
        self.path.write_bytes(b'\xff\xfe')
        before = copy.deepcopy(self.tickets)
        with self.assertRaises(StorageError):
            self.tickets = load_tickets(self.path)
        self.assertEqual(self.tickets, before)
        self.assertEqual(self.path.read_bytes(), b'\xff\xfe')

    def test_cli_converts_count_and_preserves_invalid_input_state(self):
        with patch('builtins.input', side_effect=['Laptop issue', 'Hardware', 'low', '2']):
            with redirect_stdout(StringIO()):
                handle_create_ticket(self.tickets, self.path)
        self.assertEqual(self.tickets[-1]['affected_users'], 2)
        self.assertIs(type(self.tickets[-1]['affected_users']), int)
        for value in ('2.5', 'many', '²'):
            before = copy.deepcopy(self.tickets)
            source = self.path.read_bytes()
            with patch('builtins.input', side_effect=['Issue', 'Other', 'low', value]):
                with redirect_stdout(StringIO()), self.assertRaises(ValidationError):
                    handle_create_ticket(self.tickets, self.path)
            self.assertEqual(self.tickets, before)
            self.assertEqual(self.path.read_bytes(), source)

    def test_report_tracks_reopen_and_counts_ticket_once_despite_notes(self):
        """Cross-module bug-hunter candidate for Engineer B's report module."""
        add_note(self.tickets, 'T001', 'Operator A', 'Router checked')
        add_note(self.tickets, 'T001', 'Operator B', 'Switch checked')
        assign_ticket(self.tickets, 'T001', 'Operator A')
        update_status(self.tickets, 'T001', 'in_progress')
        update_status(self.tickets, 'T001', 'resolved')
        self.assertEqual(generate_report(self.tickets)['resolution_percentage'], 100.0)
        reopen_ticket(self.tickets, 'T001')
        before = copy.deepcopy(self.tickets)
        report = generate_report(self.tickets)
        self.assertEqual((report['total'], report['unresolved'], report['resolved']), (1, 1, 0))
        self.assertEqual(report['by_status'], {'open': 1, 'in_progress': 0, 'resolved': 0})
        self.assertEqual(report['by_category']['Network'], 1)
        self.assertEqual(report['resolution_percentage'], 0.0)
        self.assertEqual(self.tickets, before)
