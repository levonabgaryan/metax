from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from django_framework.metax.views.category_helper_word.resources import (
    CATEGORY_HELPER_WORD_POST_AND_PATCH_OPENAPI_EXAMPLE,
    CategoryHelperWordPatchRequestBody,
    CategoryHelperWordPath,
    CategoryHelperWordResource,
    CategoryHelperWordResponseBody,
)
from django_framework.metax.views.json_api_controller import MetaxJsonApiController
from dmr import Body, Path, ResponseSpec, modify
from dmr.openapi.objects import MediaTypeMetadata
from pydanja import DANJAError

from metax.core.application.cud_services.category import (
    UpdateHelperWordTextRequestDTO,
    UpdateHelperWordTextService,
)
from metax_bootstrap import get_metax_lifespan_manager


class CategoryHelperWordResourceController(MetaxJsonApiController):
    @modify(
        status_code=HTTPStatus.NO_CONTENT,
        tags=["Category Helper word"],
        extra_responses=[ResponseSpec(status_code=HTTPStatus.NOT_FOUND, return_type=DANJAError)],
    )
    async def delete(self, parsed_path: Path[CategoryHelperWordPath]) -> None:
        metax_container = get_metax_lifespan_manager().get_metax_container()
        unit_of_work = metax_container.get_unit_of_work()

        async with unit_of_work as uow:
            category = await uow.category_repo.get_by_helper_word_uuid(parsed_path.helper_word_uuid)
            category.delete_helper_words_by_uuids(uuids=[parsed_path.helper_word_uuid])
            await uow.category_repo.update(category)
            await uow.commit()

    @modify(
        status_code=HTTPStatus.OK,
        tags=["Category Helper word"],
        extra_responses=[
            ResponseSpec(status_code=HTTPStatus.NOT_FOUND, return_type=DANJAError),
            ResponseSpec(status_code=HTTPStatus.CONFLICT, return_type=DANJAError),
        ],
    )
    async def patch(
        self,
        parsed_body: Annotated[
            Body[CategoryHelperWordPatchRequestBody],
            MediaTypeMetadata(example=CATEGORY_HELPER_WORD_POST_AND_PATCH_OPENAPI_EXAMPLE),
        ],
    ) -> CategoryHelperWordResponseBody:
        container = get_metax_lifespan_manager().get_metax_container()
        unit_of_work_provider = container.get_unit_of_work_provider()
        event_bus = await container.get_event_bus()

        category_identifier = parsed_body.category_identifier
        category_uuid = category_identifier.id
        helper_word = parsed_body.helper_word_text

        request_dto = UpdateHelperWordTextRequestDTO(
            category_uuid=UUID(category_uuid),
            helper_word_uuid=UUID(parsed_body.data.id),
            new_text=helper_word,
        )
        cud_service = UpdateHelperWordTextService(unit_of_work_provider=unit_of_work_provider, event_bus=event_bus)
        response_dto = await cud_service.execute(request_dto)

        return CategoryHelperWordResponseBody.from_basemodel(
            resource=CategoryHelperWordResource(
                helper_word_uuid=response_dto.helper_words_payload.helper_word_uuid,
                helper_word_text=response_dto.helper_words_payload.helper_word_text,
                created_at=response_dto.helper_words_payload.created_at,
                updated_at=response_dto.helper_words_payload.updated_at,
            )
        )
