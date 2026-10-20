"""ID generators for internal UUIDs and human-readable public ticket identifiers."""

import uuid
import threading

_counter_lock = threading.Lock()
_ticket_counter = 1000


def generate_uuid() -> uuid.UUID:
    """Generate a standard UUID4."""
    return uuid.uuid4()


def generate_public_id(prefix: str = "T") -> str:
    """Generate human-friendly ticket IDs like T-1042."""
    global _ticket_counter
    with _counter_lock:
        _ticket_counter += 1
        return f"{prefix}-{_ticket_counter}"
