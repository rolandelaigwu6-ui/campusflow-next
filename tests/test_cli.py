import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from io import StringIO
from contextlib import redirect_stdout

from main import handle_search_tickets, main, run_menu
from campusflow.exceptions import StorageError


def make_ticket():
    return {
        "id": "T001",
        "title": "WiFi connection lost",
        "category": "Network",
        "urgency": "high",
        "affected_users": 2,
        "priority": "high",
        "status": "open",
        "assigned_to": None,
    }


class SearchCliTests(unittest.TestCase):
    def test_invalid_category_reprompts_until_valid_choice(self):
        tickets = [make_ticket()]
        user_inputs = [
            "wifi",       # Title query
            "invalid",    # Invalid category
            "Network",    # Valid category retry
            "open",       # Status
            "high",       # Priority
        ]
        output = StringIO()

        with patch("builtins.input", side_effect=user_inputs) as mocked_input:
            with redirect_stdout(output):
                handle_search_tickets(tickets)

        self.assertEqual(mocked_input.call_count, 5)
        self.assertIn("Invalid category", output.getvalue())
        self.assertIn("T001", output.getvalue())
        self.assertIn("Matching tickets: 1", output.getvalue())

    def test_no_matching_tickets_displays_helpful_message(self):
        tickets = [make_ticket()]
        user_inputs = ["printer", "", "", ""]

        output = StringIO()
        with patch("builtins.input", side_effect=user_inputs):
            with redirect_stdout(output):
                handle_search_tickets(tickets)

        self.assertIn(
            "No tickets matched your search and filters.",
            output.getvalue(),
        )


    def test_startup_stops_when_storage_cannot_be_loaded(self):
        output = StringIO()

        with patch("main.load_tickets", side_effect=StorageError("Invalid JSON")):
            with patch("main.run_menu") as mocked_menu:
                with redirect_stdout(output):
                    main()

        mocked_menu.assert_not_called()
        self.assertIn(
            "Startup stopped to protect existing data",
            output.getvalue(),
        )


class MenuExitTests(unittest.TestCase):
    def test_exit_option_zero_saves_and_exits_when_confirmed(self):
        output = StringIO()

        with patch("builtins.input", side_effect=["0", "y"]):
            with patch("main.save_tickets") as mocked_save:
                with redirect_stdout(output):
                    run_menu([], "/tmp/campusflow-test-tickets.json")

        mocked_save.assert_called_once_with(
            [], "/tmp/campusflow-test-tickets.json"
        )
        self.assertIn("Tickets saved successfully", output.getvalue())

    def test_cancelling_exit_returns_to_menu(self):
        output = StringIO()

        with patch("builtins.input", side_effect=["0", "n", "0", "y"]):
            with patch("main.save_tickets") as mocked_save:
                with redirect_stdout(output):
                    run_menu([], "/tmp/campusflow-test-tickets.json")

        self.assertEqual(mocked_save.call_count, 1)
        self.assertIn("Exit cancelled", output.getvalue())
        self.assertIn("Tickets saved successfully", output.getvalue())


    def test_save_failure_does_not_report_success_or_exit(self):
        output = StringIO()

        with patch("builtins.input", side_effect=["0", "y", "0", "y"]):
            with patch(
                "main.save_tickets",
                side_effect=[StorageError("Disk is full"), None],
            ) as mocked_save:
                with redirect_stdout(output):
                    run_menu([], "/tmp/campusflow-test-tickets.json")

        self.assertEqual(mocked_save.call_count, 2)
        self.assertIn("Disk is full", output.getvalue())
        self.assertIn("Tickets saved successfully", output.getvalue())
        self.assertEqual(
            output.getvalue().count("Tickets saved successfully"), 1
        )


class MenuInterruptionTests(unittest.TestCase):
    def test_interruption_reports_success_when_save_succeeds(self):
        output = StringIO()

        with patch("builtins.input", side_effect=KeyboardInterrupt):
            with patch("main.save_tickets") as mocked_save:
                with redirect_stdout(output):
                    run_menu([], "/tmp/campusflow-test-tickets.json")

        mocked_save.assert_called_once_with(
            [], "/tmp/campusflow-test-tickets.json"
        )
        self.assertIn("Tickets saved successfully", output.getvalue())
        self.assertNotIn("Save failed", output.getvalue())

    def test_interruption_reports_error_when_save_fails(self):
        output = StringIO()

        with patch("builtins.input", side_effect=KeyboardInterrupt):
            with patch(
                "main.save_tickets",
                side_effect=StorageError("Disk is full"),
            ) as mocked_save:
                with redirect_stdout(output):
                    run_menu([], "/tmp/campusflow-test-tickets.json")

        self.assertEqual(mocked_save.call_count, 2)
        self.assertIn("First save attempt failed: Disk is full", output.getvalue())
        self.assertIn("Retry failed: Disk is full", output.getvalue())
        self.assertIn("Changes may not have been saved", output.getvalue())
        self.assertNotIn("Tickets saved successfully", output.getvalue())


    def test_interruption_retries_and_succeeds_after_first_save_failure(self):
        output = StringIO()

        with patch("builtins.input", side_effect=KeyboardInterrupt):
            with patch(
                "main.save_tickets",
                side_effect=[StorageError("Temporary disk error"), None],
            ) as mocked_save:
                with redirect_stdout(output):
                    run_menu([], "/tmp/campusflow-test-tickets.json")

        self.assertEqual(mocked_save.call_count, 2)
        self.assertIn("Retrying save once", output.getvalue())
        self.assertIn("Tickets saved successfully on retry", output.getvalue())
        self.assertNotIn("Changes may not have been saved", output.getvalue())

    def test_interruption_warns_if_both_save_attempts_fail(self):
        output = StringIO()

        with patch("builtins.input", side_effect=KeyboardInterrupt):
            with patch(
                "main.save_tickets",
                side_effect=[
                    StorageError("First disk error"),
                    StorageError("Second disk error"),
                ],
            ) as mocked_save:
                with redirect_stdout(output):
                    run_menu([], "/tmp/campusflow-test-tickets.json")

        self.assertEqual(mocked_save.call_count, 2)
        self.assertIn("Retry failed: Second disk error", output.getvalue())
        self.assertIn("Changes may not have been saved", output.getvalue())
        self.assertNotIn("Tickets saved successfully", output.getvalue())


if __name__ == "__main__":
    unittest.main()


class StartupPersistenceTests(unittest.TestCase):
    def test_fresh_start_creates_file_and_displays_location(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data" / "tickets.json"
            output = StringIO()
            with patch("main.DEFAULT_DATA_FILE", path), patch("main.run_menu") as menu:
                with redirect_stdout(output):
                    main()
            self.assertEqual(path.read_text(), "[]")
            menu.assert_called_once_with([], path.resolve())
            self.assertIn(str(path.resolve()), output.getvalue())
            self.assertIn("new empty ticket file", output.getvalue())

    def test_restart_loads_existing_records_without_replacing_file(self):
        from campusflow.tickets import create_ticket
        from campusflow.storage import save_tickets
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "tickets.json"
            tickets = []
            create_ticket(tickets, "Saved issue", "Other", "low", 1)
            save_tickets(tickets, path)
            source = path.read_bytes()
            with patch("main.DEFAULT_DATA_FILE", path), patch("main.run_menu") as menu:
                with redirect_stdout(StringIO()):
                    main()
            menu.assert_called_once_with(tickets, path.resolve())
            self.assertEqual(path.read_bytes(), source)

    def test_corrupt_file_is_preserved_on_startup(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "tickets.json"
            path.write_text("broken JSON")
            with patch("main.DEFAULT_DATA_FILE", path), patch("main.run_menu") as menu:
                with redirect_stdout(StringIO()):
                    main()
            menu.assert_not_called()
            self.assertEqual(path.read_text(), "broken JSON")
