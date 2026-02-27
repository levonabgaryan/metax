import uuid
from uuid import UUID

from adrf.viewsets import ViewSet
from adrf.requests import AsyncRequest
from dependency_injector.wiring import inject, Provide

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action

from discount_service.core.application.commands_handlers.category import (
    CreateCategoryCommand,
    CreateCategoryCommandHandler,
)
from discount_service.core.application.event_handlers.event_bus import EventBus
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer
from django_framework.discount_service.serializers.category import CreateCategorySerializer


class CategoryViewSet(ViewSet):
    @action(detail=False, methods=["post"], url_path="create")
    @inject
    async def create_new(
        self,
        request: AsyncRequest,
        unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
        event_bus: EventBus = Provide[ServiceContainer.patterns_container.container.event_bus],
    ) -> Response:
        # api/category/create/
        serializer = CreateCategorySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        category_uuid = uuid.uuid4()
        cmd = CreateCategoryCommand(
            category_uuid=category_uuid,
            name=serializer.validated_data["category_name"],
            helper_words=frozenset(serializer.validated_data["helper_words"]),
        )
        command_handler = CreateCategoryCommandHandler(unit_of_work=unit_of_work, mediator=event_bus)
        await command_handler.handle_command(cmd)

        return Response({"message": f"Category is created with {category_uuid} uuid"}, status=201)

    @action(detail=False, methods=["get"], url_path="get")
    @inject
    async def get_by_uuid(
        self,
        request: AsyncRequest,
        unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
    ) -> Response:
        # api/categories/get/?category_uuid=<uuid_value>
        uuid_str = request.query_params.get("category_uuid")

        if not uuid_str:
            return Response({"error": "category_uuid is required"}, status=status.HTTP_400_BAD_REQUEST)

        repo = unit_of_work.category_repo
        category = await repo.get_by_uuid(UUID(uuid_str))

        return Response({"message": f"Category is found with {category.get_uuid()}"}, status=200)
