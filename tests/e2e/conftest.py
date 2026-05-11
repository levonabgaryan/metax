import pytest
from _pytest.monkeypatch import MonkeyPatch

from metax.core.domain.entities.retailer.value_objects import RetailersNames
from tests.utils import FakeDiscountedProductsCreator


@pytest.fixture
def fake_collectors(monkeypatch: MonkeyPatch) -> type[FakeDiscountedProductsCreator]:
    from metax.frameworks_and_drivers.taskiq_framework import tasks

    FakeDiscountedProductsCreator.SPECS_BY_RETAILER_NAME = {}

    monkeypatch.setattr(
        tasks,
        "RETAILER_NAME_DISCOUNTED_PRODUCT_COLLECTOR_SERVICE_CREATOR_MAP",
        {
            RetailersNames.SAS_AM: FakeDiscountedProductsCreator,
            RetailersNames.YEREVAN_CITY: FakeDiscountedProductsCreator,
        },
    )
    monkeypatch.setattr(tasks, "SasAmDiscountProductCollectorCreator", FakeDiscountedProductsCreator)
    monkeypatch.setattr(tasks, "YerevanCityDiscountProductCollectorCreator", FakeDiscountedProductsCreator)

    return FakeDiscountedProductsCreator
