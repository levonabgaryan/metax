import datetime as dt
from dataclasses import dataclass

from metax.core.application.event_handlers.event import Event


@dataclass(frozen=True)
class NewDiscountedProductsFromRetailerCollected(Event):
    new_products_created_date: dt.datetime


@dataclass(frozen=True)
class OldDiscountedProductsDeleted(Event):
    new_discounted_products_creation_date: dt.datetime
