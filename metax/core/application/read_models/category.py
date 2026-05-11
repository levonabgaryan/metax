from typing import Required, TypedDict


class CategoryHelperWordReadModel(TypedDict):
    """Category helper word read model for Category read model."""

    uuid_: Required[str]
    created_at: Required[str]
    updated_at: Required[str]
    helper_word_text: Required[str]


class CategoryReadModel(TypedDict):
    uuid_: Required[str]
    created_at: Required[str]
    updated_at: Required[str]
    name: Required[str]
    helper_words: Required[list[CategoryHelperWordReadModel]]
