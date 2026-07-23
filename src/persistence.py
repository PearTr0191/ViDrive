"""Persistence layer for ViDrive — save/load results to ~/.vidrive/history.json."""
import json
import os
from pathlib import Path
from datetime import datetime
from src.config import HISTORY_DIR, HISTORY_FILE, MAX_HISTORY_ENTRIES


def _history_path() -> Path:
    """Resolve the history file path, expanding ~ to the user's home directory."""
    home = Path(os.path.expanduser(HISTORY_DIR))
    return home / HISTORY_FILE


def _ensure_dir() -> None:
    """Create the history directory if it doesn't exist."""
    home = Path(os.path.expanduser(HISTORY_DIR))
    home.mkdir(parents=True, exist_ok=True)


def save_result(name: str, result_data: dict) -> str:
    """Save a calculation result to history.

    Args:
        name: Human-readable name for the result (e.g., "vios_hanoi_2026").
        result_data: Dictionary containing the result and metadata.

    Returns:
        The path to the history file.
    """
    _ensure_dir()
    path = _history_path()

    history: list[dict] = []
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                history = json.load(f)
                if not isinstance(history, list):
                    history = []
        except (json.JSONDecodeError, OSError):
            history = []

    entry = {
        "name": name,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "data": result_data,
    }

    # Check if name already exists — replace it
    for i, existing in enumerate(history):
        if existing.get("name") == name:
            history[i] = entry
            break
    else:
        history.append(entry)

    # Trim to max entries (keep most recent)
    if len(history) > MAX_HISTORY_ENTRIES:
        history = history[-MAX_HISTORY_ENTRIES:]

    with path.open("w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return str(path)


def load_history() -> list[dict]:
    """Load all saved results from history.

    Returns:
        List of history entries, each with 'name', 'timestamp', and 'data'.
    """
    path = _history_path()
    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as f:
            history = json.load(f)
            if isinstance(history, list):
                return history
            return []
    except (json.JSONDecodeError, OSError):
        return []


def load_result(name: str) -> dict | None:
    """Load a specific saved result by name.

    Args:
        name: The name of the saved result.

    Returns:
        The result data dictionary, or None if not found.
    """
    history = load_history()
    for entry in history:
        if entry.get("name") == name:
            return entry.get("data")
    return None


def delete_result(name: str) -> bool:
    """Delete a saved result by name.

    Returns:
        True if the result was found and deleted, False otherwise.
    """
    path = _history_path()
    if not path.exists():
        return False

    history = load_history()
    new_history = [e for e in history if e.get("name") != name]

    if len(new_history) == len(history):
        return False  # Nothing was deleted

    with path.open("w", encoding="utf-8") as f:
        json.dump(new_history, f, ensure_ascii=False, indent=2)

    return True


def clear_history() -> int:
    """Clear all saved results.

    Returns:
        The number of entries that were cleared.
    """
    path = _history_path()
    if not path.exists():
        return 0

    count = len(load_history())
    path.unlink(missing_ok=True)
    return count
