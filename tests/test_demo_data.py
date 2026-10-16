"""Verify portable demo records and protection of existing local data."""
import tempfile
import unittest
from pathlib import Path

from campusflow.notes import add_note
from campusflow.storage import load_tickets, save_tickets
from campusflow.tickets import create_ticket
from prepare_demo import PROJECT_ROOT, prepare_demo


class DemoDataTests(unittest.TestCase):
    def test_demo_load_save_and_id_continuity(self):
        source = PROJECT_ROOT / 'examples' / 'demo-tickets.json'
        original = source.read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'data' / 'tickets.json'
            prepare_demo(target)
            tickets = load_tickets(target)
            self.assertEqual(len(tickets), 4)
            self.assertEqual({ticket['status'] for ticket in tickets}, {'open', 'in_progress', 'resolved'})
            self.assertTrue(any(ticket['notes'] for ticket in tickets))
            self.assertEqual(create_ticket(tickets, 'Demo continuation', 'Other', 'low', 1)['id'], 'T005')
            self.assertEqual(add_note(tickets, 'T001', 'Demo Operator', 'Follow-up confirmed')['note_id'], 'N002')
            save_tickets(tickets, target)
            self.assertEqual(load_tickets(target), tickets)
        self.assertEqual(source.read_bytes(), original)

    def test_demo_never_overwrites_existing_storage(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'tickets.json'
            for content in ('[]', 'broken JSON', '[{"important": "existing records"}]'):
                with self.subTest(content=content):
                    target.write_text(content)
                    with self.assertRaises(FileExistsError):
                        prepare_demo(target)
                    self.assertEqual(target.read_text(), content)
