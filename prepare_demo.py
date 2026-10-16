"""Copy tracked dummy tickets into fresh local storage without replacing records."""
import json
from pathlib import Path

from campusflow.exceptions import StorageError
from campusflow.storage import load_tickets

PROJECT_ROOT = Path(__file__).resolve().parent


def prepare_demo(destination=None):
    """Validate the example and exclusively create the destination; never overwrite."""
    source = PROJECT_ROOT / "examples" / "demo-tickets.json"
    target = Path(destination) if destination is not None else PROJECT_ROOT / "data" / "tickets.json"
    tickets = load_tickets(source)
    if not tickets:
        raise StorageError("The demonstration fixture must contain tickets.")
    target.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation also protects an existing empty or malformed file.
    with target.open("x", encoding="utf-8") as output:
        json.dump(tickets, output, indent=2)
        output.write("\n")
    return target.resolve()


if __name__ == "__main__":
    try:
        path = prepare_demo()
    except FileExistsError:
        print("Demo not installed: data/tickets.json already exists. Existing records were preserved.")
        raise SystemExit(1)
    except (OSError, StorageError) as error:
        print(f"Demo not installed: {error}")
        raise SystemExit(1)
    print(f"Demo tickets saved to {path}. Run python main.py and choose View All Tickets.")
