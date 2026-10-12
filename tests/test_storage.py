"""Unit tests for F7 JSON storage persistence in CampusFlow."""

import json
import os
import shutil
import tempfile
import unittest

from campusflow.exceptions import StorageError
from campusflow.storage import load_tickets, save_tickets


class StorageTests(unittest.TestCase):
    """Test suite for saving and loading tickets via JSON persistence."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage_file = os.path.join(self.test_dir, "tickets.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_load_non_existent_file_returns_empty_list(self):
        """Loading from a nonexistent path returns an empty list (fresh start)."""
        non_existent = os.path.join(self.test_dir, "missing.json")
        tickets = load_tickets(non_existent)
        self.assertEqual(tickets, [])

    def test_save_and_load_round_trip(self):
        """Saving tickets and then loading produces the exact same records."""
        sample_tickets = [
            {
                "id": "T001",
                "title": "Wi-Fi down",
                "category": "Network",
                "urgency": "high",
                "affected_users": 15,
                "priority": "critical",
                "status": "open",
                "assigned_to": None,
            },
            {
                "id": "T002",
                "title": "Mouse broken",
                "category": "Hardware",
                "urgency": "low",
                "affected_users": 1,
                "priority": "low",
                "status": "in_progress",
                "assigned_to": "Ada",
            },
        ]
        save_tickets(sample_tickets, self.storage_file)
        self.assertTrue(os.path.exists(self.storage_file))

        loaded = load_tickets(self.storage_file)
        self.assertEqual(loaded, sample_tickets)

    def test_save_creates_nested_directories_automatically(self):
        """save_tickets creates any missing parent directories."""
        nested_file = os.path.join(self.test_dir, "data", "subfolder", "tickets.json")
        sample_tickets = [{"id": "T001", "title": "Test"}]
        save_tickets(sample_tickets, nested_file)
        self.assertTrue(os.path.exists(nested_file))
        loaded = load_tickets(nested_file)
        self.assertEqual(loaded, sample_tickets)

    def test_load_corrupted_json_raises_storage_error_and_preserves_file(self):
        """Corrupted JSON raises StorageError without deleting the corrupted file."""
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{invalid json content, missing brackets:")

        with self.assertRaises(StorageError):
            load_tickets(self.storage_file)

        # File must NOT be deleted
        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("invalid json content", content)

    def test_load_non_list_json_raises_storage_error(self):
        """If JSON contains a root object that is not a list, raise StorageError."""
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump({"not": "a list"}, f)

        with self.assertRaises(StorageError):
            load_tickets(self.storage_file)

    def test_load_list_with_non_dict_elements_raises_storage_error(self):
        """If JSON list contains elements that are not dicts, raise StorageError."""
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(["string_item", 123], f)

        with self.assertRaises(StorageError):
            load_tickets(self.storage_file)

    def test_save_non_list_raises_storage_error(self):
        """Passing a non-list to save_tickets raises StorageError."""
        with self.assertRaises(StorageError):
            save_tickets({"not": "a list"}, self.storage_file)  # type: ignore


if __name__ == "__main__":
    unittest.main()
