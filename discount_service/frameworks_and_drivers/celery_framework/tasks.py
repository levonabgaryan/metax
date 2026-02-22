from .celery_application import celery_app


@celery_app.task(name="CollectDiscountedProducts")
async def celery_task_collect_discounted_products_from_all_retailers() -> None:
    pass
