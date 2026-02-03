import uuid
from uuid import UUID

from adrf.viewsets import ViewSet
from adrf.requests import AsyncRequest
from dependency_injector.wiring import inject, Provide

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action

from discount_service.core.application.commands_and_handlers.cud.category import CreateCategoryCommand
from discount_service.core.application.patterns.message_buss import MessageBus
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer
from django_framework.discount_service.serializers.category import CreateCategorySerializer


class CategoryViewSet(ViewSet):
    @action(detail=False, methods=["post"], url_path="create")
    @inject
    async def create_new(
        self,
        request: AsyncRequest,
        message_bus: MessageBus = Provide[ServiceContainer.patterns_container.container.message_bus],
    ) -> Response:
        serializer = CreateCategorySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        category_uuid = uuid.uuid4()
        cmd = CreateCategoryCommand(
            category_uuid=category_uuid,
            name=serializer.validated_data["category_name"],
            helper_words=frozenset(serializer.validated_data["helper_words"]),
        )
        await message_bus.handle(cmd)

        return Response({"message": f"Category is created with {category_uuid} uuid"}, status=201)

    @action(detail=False, methods=["get"], url_path="get")
    @inject
    async def get_by_uuid(
        self,
        request: AsyncRequest,
        unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
    ) -> Response:
        uuid_str = request.query_params.get("category_uuid")

        if not uuid_str:
            return Response({"error": "category_uuid is required"}, status=status.HTTP_400_BAD_REQUEST)

        async with unit_of_work as uow:
            repo = uow.category_repo
            category = await repo.get_by_uuid(UUID(uuid_str))

        return Response({"message": f"Category is found with {category.get_uuid()}"}, status=200)
