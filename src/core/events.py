"""Domain events and in-process EventBus for decoupled module communication."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Type


@dataclass
class DomainEvent:
    """Base class for all domain events."""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def event_name(self) -> str:
        return self.__class__.__name__


HandlerFunc = Callable[[Any], Any]


class EventBus:
    """In-process event bus supporting in-transaction and after-commit handler execution."""

    def __init__(self) -> None:
        self._in_tx_handlers: Dict[Type[DomainEvent], List[HandlerFunc]] = {}
        self._after_commit_handlers: Dict[Type[DomainEvent], List[HandlerFunc]] = {}

    def subscribe_in_tx(self, event_type: Type[DomainEvent], handler: HandlerFunc) -> None:
        """Subscribes handler that executes inside the active DB transaction."""
        if event_type not in self._in_tx_handlers:
            self._in_tx_handlers[event_type] = []
        self._in_tx_handlers[event_type].append(handler)

    def subscribe_after_commit(self, event_type: Type[DomainEvent], handler: HandlerFunc) -> None:
        """Subscribes handler that executes strictly after transaction commit."""
        if event_type not in self._after_commit_handlers:
            self._after_commit_handlers[event_type] = []
        self._after_commit_handlers[event_type].append(handler)

    def publish_in_tx(self, event: DomainEvent, context: Any = None) -> None:
        """Executes in-transaction handlers for the event."""
        handlers = self._in_tx_handlers.get(type(event), [])
        for handler in handlers:
            handler(event, context) if context is not None else handler(event)

    def publish_after_commit(self, event: DomainEvent) -> None:
        """Executes after-commit handlers for the event."""
        handlers = self._after_commit_handlers.get(type(event), [])
        for handler in handlers:
            handler(event)


# Global event bus singleton
event_bus = EventBus()
