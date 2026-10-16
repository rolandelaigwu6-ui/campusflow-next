"""JSON storage and safe persistence for CampusFlow Next."""

import json
import os
import shutil
import tempfile
from datetime import datetime
from typing import Any, Dict, List

from campusflow.exceptions import StorageError
from campusflow.tickets import calculate_priority
from campusflow.validation import validate_ticket_dict


def _create_timestamped_backup(filepath: str) -> None:
    """Preserve an existing ticket file before it is replaced."""
    if not os.path.isfile(filepath):
        return

    directory = os.path.dirname(filepath) or "."
    backup_dir = os.path.join(directory, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    filename = f"{os.path.basename(filepath)}-{timestamp}.json"
    backup_path = os.path.join(backup_dir, filename)

    shutil.copy2(filepath, backup_path)


def save_tickets(tickets: List[Dict[str, Any]], filepath: str) -> None:
    """Atomically save the list of tickets to a JSON file.

    Args:
        tickets: List of ticket dictionaries.
        filepath: Target file path.

    Raises:
        StorageError: If the directory cannot be created, data is malformed, or writing fails.
    """
    if not isinstance(tickets, list):
        raise StorageError("Tickets must be provided as a list.")

    # Protect existing tickets from accidental empty saves.
    if not tickets and os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as existing_file:
                existing_data = json.load(existing_file)
        except (OSError, json.JSONDecodeError, UnicodeError) as e:
            raise StorageError(
                f"Refusing to overwrite existing file '{filepath}' "
                f"with an empty list because its contents cannot be safely checked: {e}"
            ) from e

        if not isinstance(existing_data, list):
            raise StorageError(
                f"Refusing to overwrite '{filepath}' with an empty list: "
                "the existing file does not contain a ticket list."
            )

        if existing_data:
            raise StorageError(
                f"Refusing to overwrite '{filepath}' with an empty list "
                "because it already contains tickets."
            )

    # Validate all tickets before saving to ensure state integrity
    seen_ids = set()
    for idx, ticket in enumerate(tickets):
        validate_ticket_dict(ticket, calculate_priority_fn=calculate_priority)
        tid = ticket["id"]
        if tid in seen_ids:
            raise StorageError(f"Cannot save tickets: Duplicate ticket ID '{tid}' detected.")
        seen_ids.add(tid)

    dir_name = os.path.dirname(filepath)
    if dir_name:
        try:
            os.makedirs(dir_name, exist_ok=True)
        except OSError as e:
            raise StorageError(f"Failed to create directory '{dir_name}': {e}") from e

    temp_dir = dir_name if dir_name else "."
    try:
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", dir=temp_dir, delete=False, encoding="utf-8"
        )
        try:
            json.dump(tickets, temp_file, indent=2)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_file.close()
            _create_timestamped_backup(filepath)
            os.replace(temp_file.name, filepath)
        except Exception:
            if os.path.exists(temp_file.name):
                try:
                    os.remove(temp_file.name)
                except OSError:
                    pass
            raise
    except OSError as e:
        raise StorageError(f"Failed to save tickets to '{filepath}': {e}") from e
    except (TypeError, ValueError) as e:
        raise StorageError(f"Data serialization error while saving tickets: {e}") from e


def load_tickets(filepath: str) -> List[Dict[str, Any]]:
    """Load tickets from a JSON file with full collection validation.

    If the file does not exist, returns an empty list for a fresh start.
    If the file exists but contains corrupted JSON, invalid records, duplicate IDs,
    or schema violations, raises StorageError without modifying the file or in-memory state.

    Args:
        filepath: Target file path.

    Returns:
        List of validated ticket dictionaries.

    Raises:
        StorageError: If the file is unreadable, malformed, or fails collection validation.
    """
    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise StorageError(
            f"Corrupted ticket file '{filepath}': Malformed JSON (line {e.lineno}, col {e.colno})."
        ) from e
    except OSError as e:
        raise StorageError(f"Cannot read ticket file '{filepath}': {e}") from e

    if not isinstance(data, list):
        raise StorageError(
            f"Invalid ticket data in '{filepath}': Expected a list of tickets, got {type(data).__name__}."
        )

    # Work on copies: a failed validation must not leave partially migrated
    # decoded records behind, and the caller receives data only after all pass.
    validated_data = []
    seen_ticket_ids = set()

    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise StorageError(
                f"Invalid ticket data in '{filepath}' at index {idx}: Expected a ticket dictionary, got {type(item).__name__}."
            )

        ticket = dict(item)

        # Backward compatibility migration: ensure 'notes' key is present.
        if "notes" not in ticket:
            ticket["notes"] = []

        validate_ticket_dict(ticket, calculate_priority_fn=calculate_priority)

        tid = ticket["id"]
        if tid in seen_ticket_ids:
            raise StorageError(
                f"Corrupted ticket file '{filepath}': Duplicate ticket ID '{tid}' found."
            )
        seen_ticket_ids.add(tid)
        validated_data.append(ticket)

    return validated_data
