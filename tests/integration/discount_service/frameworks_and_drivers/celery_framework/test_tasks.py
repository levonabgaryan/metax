from celery.schedules import crontab


#
# @pytest.mark.django_db(transaction=True)
# @pytest.mark.asyncio
# @inject
# async def test_collect_discounted_products_from_retailer_success(
#     unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
# ) -> None:
#     # given
#     retailer = make_retailer_entity()
#     await unit_of_work.retailer_repo.add(retailer)
#
#     batches = [
#         batch
#         async for batch in mock_create_many_discounted_products_from_retailer(
#             discounted_product_counts=5, retailer_uuid=retailer.get_uuid()
#         )
#     ]
#
#     expected_products = [p for batch in batches for p in batch]
#
#     async def mock_gen(*args: Any, **kwargs: Any) -> AsyncIterator[list[DiscountedProduct]]:
#         for batch in batches:
#             yield batch
#             await asyncio.sleep(0.0)
#
#     mocked_factory_class = Mock(spec=DiscountedProductFactory)
#     mocked_factory_class.create_many_from_retailer.side_effect = mock_gen
#
#     # when
#     with get_current_container_for_tests().patterns_container.container.discounted_product_factory.override(
#         mocked_factory_class
#     ):
#         await collect_discounted_products_from_all_retailers()
#
#     # then
#     count = 0
#     async for product in unit_of_work.discounted_product_repo.get_all():
#         count += 1
#         assert product in expected_products
#     assert count == len(expected_products)
#


def test_collect_products_task_schedule() -> None:
    from discount_service.frameworks_and_drivers.celery_framework.celery_application import celery_app

    task_name = "run-daily-task-at-0100"

    assert task_name in celery_app.conf.beat_schedule

    schedule_entry = celery_app.conf.beat_schedule[task_name]

    assert schedule_entry["task"] == "tasks.collect_discounted_products_from_retailer"

    schedule = schedule_entry["schedule"]
    assert isinstance(schedule, crontab)
    assert schedule.hour == {1}  # type: ignore[attr-defined]
    assert schedule.minute == {0}  # type: ignore[attr-defined]
