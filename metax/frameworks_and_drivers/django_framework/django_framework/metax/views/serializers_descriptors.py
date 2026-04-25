from dmr.internal.context import SerializerContext


class PydanticSerializerContext(SerializerContext):
    strict_validation = True
