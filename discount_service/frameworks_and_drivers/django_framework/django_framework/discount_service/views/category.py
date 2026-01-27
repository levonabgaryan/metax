from adrf.viewsets import ViewSet
from adrf.requests import AsyncRequest

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action

from django_framework.discount_service.serializers.category import CreateCategorySerializer


class CategoryViewSet(ViewSet):
    @action(detail=False, methods=["post"], url_path="create")
    async def create_new(self, request: AsyncRequest) -> Response:
        serializer = CreateCategorySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Async create works!"}, status=201)
