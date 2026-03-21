from typing import TypedDict, Any


class IndexMetadata(TypedDict):
    index_name: str
    alias_name: str
    index_body: dict[str, Any]
