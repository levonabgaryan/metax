from adrf.serializers import Serializer  # type: ignore[import-untyped]
from rest_framework import serializers


class CreateCategorySerializer(Serializer):  # type: ignore[misc]
    category_name = serializers.CharField()
    helper_words = serializers.ListSerializer(child=serializers.CharField())
