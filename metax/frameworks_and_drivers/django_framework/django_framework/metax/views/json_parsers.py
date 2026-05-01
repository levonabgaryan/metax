from dmr.parsers import JsonParser
from dmr.renderers import JsonRenderer


class JsonApiParser(JsonParser):
    def __init__(self) -> None:
        super().__init__(content_type="application/vnd.api+json")


class JsonApiRenderer(JsonRenderer):
    def __init__(self) -> None:
        super().__init__(content_type="application/vnd.api+json")
