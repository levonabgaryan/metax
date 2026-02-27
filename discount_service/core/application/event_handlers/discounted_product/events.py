from dataclasses import dataclass
from datetime import datetime

from discount_service.core.application.event_handlers.event import Event


@dataclass(frozen=True)
class NewDiscountedProductsFromRetailerCollected(Event):
    new_products_created_date: datetime


@dataclass(frozen=True)
class OldDiscountedProductsDeleted(Event):
    new_discounted_products_creation_date: datetime
