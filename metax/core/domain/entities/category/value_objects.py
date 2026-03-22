from __future__ import annotations

from dataclasses import dataclass

from metax.core.domain.ddd_patterns import ValueObject


@dataclass(frozen=True, unsafe_hash=False, eq=True, slots=True)
class CategoryHelperWords(ValueObject):
    words: frozenset[str]
