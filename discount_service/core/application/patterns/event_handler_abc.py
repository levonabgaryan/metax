from __future__ import annotations

from abc import abstractmethod

from discount_service.core.application.patterns.mediator import BaseHandler


class EventHandler[GenericEvent](BaseHandler):
    @abstractmethod
    async def handle_event(self, event: GenericEvent) -> None:
        pass
