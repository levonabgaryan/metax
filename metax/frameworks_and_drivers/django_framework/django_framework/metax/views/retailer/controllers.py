import uuid
from http import HTTPStatus

from django_framework.metax.views.retailer.request_body_models import CreateRetailerRequestBodyModel
from django_framework.metax.views.retailer.response_body_models import CreateRetailerResponseBodyModel
from dmr import Body, Controller, modify
from dmr.plugins.pydantic import PydanticSerializer

from metax.core.application.cud_services.retailer import CreateRetailerRequestDTO, CreateRetailerService
from metax_bootstrap import get_metax_lifespan_manager


class CreateRetailerController(Controller[PydanticSerializer]):
    @modify(
        status_code=HTTPStatus.CREATED,
        tags=["Retailer"],
    )
    async def post(self, parsed_body: Body[CreateRetailerRequestBodyModel]) -> CreateRetailerResponseBodyModel:
        container = get_metax_lifespan_manager().get_di_container()
        patterns = container.patterns_container.container
        unit_of_work_provider = patterns.unit_of_work_provider()
        event_bus = await patterns.event_bus.async_()

        retailer_uuid = uuid.uuid7()
        request_dto = CreateRetailerRequestDTO(
            retailer_uuid=retailer_uuid,
            name=parsed_body.name,
            url=parsed_body.url,
            phone_number=parsed_body.phone_number,
        )

        service = CreateRetailerService(
            unit_of_work_provider=unit_of_work_provider,
            event_bus=event_bus,
        )
        await service.execute(request_dto)

        return CreateRetailerResponseBodyModel(retailer_uuid=retailer_uuid)
