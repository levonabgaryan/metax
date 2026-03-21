from adrf.serializers import Serializer
from rest_framework import serializers


class CreateCategorySerializer(Serializer):
    category_name = serializers.CharField()
    helper_words = serializers.ListSerializer(child=serializers.CharField())
