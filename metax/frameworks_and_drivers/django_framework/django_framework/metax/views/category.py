import uuid
from uuid import UUID

from adrf.viewsets import ViewSet
from adrf.requests import AsyncRequest

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action

from metax.core.application.commands_handlers.category import (
    CreateCategoryCommand,
    CreateCategoryCommandHandler,
)
from metax.frameworks_and_drivers.di.metax_container import get_metax_container
from django_framework.metax.serializers.category import CreateCategorySerializer


class CategoryViewSet(ViewSet):
    @action(detail=False, methods=["post"], url_path="create")
    async def create_new(self, request: AsyncRequest) -> Response:
        # api/category/create/
        container = get_metax_container()
        unit_of_work = await container.patterns_container.container.unit_of_work.async_()
        event_bus = container.patterns_container.container.event_bus()

        serializer = CreateCategorySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        category_uuid = uuid.uuid4()
        cmd = CreateCategoryCommand(
            category_uuid=category_uuid,
            name=serializer.validated_data["category_name"],
            helper_words=frozenset(serializer.validated_data["helper_words"]),
        )
        command_handler = CreateCategoryCommandHandler(unit_of_work=unit_of_work, event_bus=event_bus)
        await command_handler.handle_command(cmd)

        return Response({"message": f"Category is created with {category_uuid} uuid"}, status=201)

    @action(detail=False, methods=["get"], url_path="get")
    async def get_by_uuid(self, request: AsyncRequest) -> Response:
        # api/categories/get/?category_uuid=<uuid_value>
        container = get_metax_container()
        unit_of_work = await container.patterns_container.container.unit_of_work.async_()

        uuid_str = request.query_params.get("category_uuid")

        if not uuid_str:
            return Response({"error": "category_uuid is required"}, status=status.HTTP_400_BAD_REQUEST)

        repo = unit_of_work.category_repo
        category = await repo.get_by_uuid(UUID(uuid_str))

        return Response({"message": f"Category is found with {category.get_uuid()}"}, status=200)
