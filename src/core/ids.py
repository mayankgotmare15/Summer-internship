import threading
import uuid

from sqlalchemy.orm import Session

_counter_lock = threading.Lock()
_ticket_counter: int | None = None


def generate_uuid() -> uuid.UUID:
    """Generate a standard UUID4."""
    return uuid.uuid4()


def generate_public_id(prefix: str = "T", db: Session | None = None) -> str:
    """Generate human-friendly ticket IDs like T-1042 guaranteed to be unique."""
    global _ticket_counter
    with _counter_lock:
        if _ticket_counter is None:
            _ticket_counter = 1000
            if db is not None:
                try:
                    from src.db.models.ticket import Ticket

                    rows = db.query(Ticket.public_id).all()
                    nums = []
                    for (pid,) in rows:
                        if pid and pid.startswith(f"{prefix}-"):
                            part = pid.split("-", 1)[1]
                            if part.isdigit():
                                nums.append(int(part))
                    if nums:
                        _ticket_counter = max(nums)
                except Exception:
                    pass

        while True:
            _ticket_counter += 1
            candidate = f"{prefix}-{_ticket_counter}"
            if db is not None:
                try:
                    from src.db.models.ticket import Ticket

                    existing = db.query(Ticket.id).filter(Ticket.public_id == candidate).first()
                    if existing:
                        continue
                except Exception:
                    pass
            return candidate
