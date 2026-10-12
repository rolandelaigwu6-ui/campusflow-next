"""JSON storage and persistence for CampusFlow."""

import json
import os
import tempfile
from typing import Any, Dict, List

from campusflow.exceptions import StorageError


def save_tickets(tickets: List[Dict[str, Any]], filepath: str) -> None:
    """Atomically save the list of tickets to a JSON file.

    Args:
        tickets: List of ticket dictionaries.
        filepath: Target file path.

    Raises:
        StorageError: If the directory cannot be created or file writing fails.
    """
    if not isinstance(tickets, list):
        raise StorageError("Tickets must be provided as a list.")

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
    """Load tickets from a JSON file.

    If the file does not exist, returns an empty list for a fresh start.
    If the file exists but contains corrupted or invalid JSON, raises StorageError
    without deleting the file.

    Args:
        filepath: Target file path.

    Returns:
        List of ticket dictionaries.

    Raises:
        StorageError: If the file is unreadable or malformed.
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

    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise StorageError(
                f"Invalid ticket data in '{filepath}' at index {idx}: Expected a ticket dictionary, got {type(item).__name__}."
            )

    return data
