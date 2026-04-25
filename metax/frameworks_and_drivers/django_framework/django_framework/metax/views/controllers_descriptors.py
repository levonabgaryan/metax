from django_framework.metax.views.serializers_descriptors import PydanticSerializerContext
from dmr.endpoint import Endpoint


class BaseController(Endpoint):
    serializer_context_cls = PydanticSerializerContext
