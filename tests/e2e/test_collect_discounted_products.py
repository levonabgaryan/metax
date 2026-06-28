import datetime as dt
import json
from decimal import Decimal
from typing import Any

import pytest
from dmr.test import DMRAsyncClient

from metax.frameworks_and_drivers.taskiq_framework import tasks
from metax.frameworks_and_drivers.taskiq_framework.tasks import (
    taskiq_collect_discounted_products_from_all_retailers,
)
from metax_lifespan import MetaxAppLifespanManager
from tests.utils import (
    FakeDiscountedProductsCreator,
    FakeProductSpec,
    make_retailer_entity,
)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_collected_products_appear_in_read_model(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
    dmr_async_client: DMRAsyncClient,
    fake_collectors: type[FakeDiscountedProductsCreator],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    container = metax_lifespan_manager_for_tests.get_metax_container()
    uow = container.get_unit_of_work()

    sas_am = make_retailer_entity(name="sas-am")
    async with uow as u:
        await u.retailer_repo.add(sas_am)
        await u.commit()

    fake_collectors.SPECS_BY_RETAILER_NAME["sas-am"] = [
        FakeProductSpec(name="lays chips 100g", real_price=Decimal(1000), discounted_price=Decimal(700)),
        FakeProductSpec(name="coca cola 1.5L", real_price=Decimal(800), discounted_price=Decimal(600)),
    ]

    # Step 1 (collection) enqueues step 2 (embedding) via the broker; run step 2 inline here so the
    # read model is populated without a live worker. Embedding hits the model service, so it may be slow.
    async def _run_embed_inline(**kwargs: Any) -> None:
        await tasks.taskiq_embed_discounted_products(**kwargs)

    monkeypatch.setattr(tasks.taskiq_embed_discounted_products, "kiq", _run_embed_inline)
    await taskiq_collect_discounted_products_from_all_retailers()

    response = await dmr_async_client.get(
        path="/api/discountedProduct?page[offset]=0&page[limit]=10&filter[match][discountedProduct.name]=lays",
        content_type="application/vnd.api+json",
    )
    assert response.status_code == 200
    body = json.loads(response.content)
    assert len(body["data"]) == 1
    assert body["data"][0]["attributes"]["name"] == "lays chips 100g"

    attrs = body["data"][0]["attributes"]
    assert attrs["name"] == "lays chips 100g"

    created_at = dt.datetime.fromisoformat(attrs["createdAt"])
    updated_at = dt.datetime.fromisoformat(attrs["updatedAt"])
    assert created_at.tzinfo is not None, "JSON:API timestamps must be timezone-aware"
    assert created_at <= updated_at
    assert abs((dt.datetime.now(dt.UTC) - created_at).total_seconds()) < 60
