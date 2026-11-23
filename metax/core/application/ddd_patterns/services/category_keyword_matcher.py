"""Exact keyword rules for product categorization — the high-precision first tier of the classifier.

Retailer product names follow a stable pattern: the product noun first, then the brand in guillemets,
then size details — ``Շամպուն «Dove Ultra Care» 400մլ``. Only the part before the brand describes
*what* the product is; brand and size words are noise that pulls an embedding toward the wrong
category. So matching runs on that leading noun phrase (``product_noun_phrase``).

Each category owns a curated list of keyword phrases (``Category.keywords``). A phrase matches when its
words appear consecutively in the noun phrase. A keyword word of ``_MIN_STEM_LENGTH`` letters or more
also matches longer words that start with it, which covers Armenian endings (``շոկոլադ`` matches
``շոկոլադե``, ``կոնֆետ`` matches ``կոնֆետների``); shorter keyword words match exactly, so ``ձու``
(egg) never matches ``ձուկ`` (fish).

When several keywords match, the most specific one wins, ranked by: more words (``միցելային ջուր``
beats ``ջուր``), then the earliest position (the head noun comes first), then the longer keyword
(``շաքարաման`` beats the stem ``շաքար``). A phrase listed under more than one category is ambiguous
and is ignored — the admin rejects such edits, this is the runtime safety net.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from uuid import UUID

    from metax.core.domain.entities.category.aggregate_root_entity import Category

logger = logging.getLogger(__name__)

# Keyword words at least this long also match words that start with them (Armenian inflection).
_MIN_STEM_LENGTH = 4

# Runs of letters only: digits, punctuation and pack sizes split words apart.
_WORD_RE = re.compile(r"[^\W\d_]+")

# The brand starts at the first opening quote; everything before it is the product noun phrase.
_BRAND_START_RE = re.compile(r"[«\"“„]")

type KeywordPhrase = tuple[str, ...]


def keyword_words(text: str) -> KeywordPhrase:
    """Normalize text into the lower-cased word sequence used on both sides of matching.

    Returns:
        The words of ``text``, lower-cased, with digits and punctuation dropped.
    """
    return tuple(word.lower() for word in _WORD_RE.findall(text))


def product_noun_phrase(name: str) -> str:
    """Return the part of a product name that says what the product is (before the brand).

    Returns:
        The text before the first opening quote, or the whole name when it starts with the brand.
    """
    head = _BRAND_START_RE.split(name, maxsplit=1)[0].strip()
    return head or name


def find_keyword_conflicts(keywords_by_owner: Mapping[str, Iterable[str]]) -> dict[KeywordPhrase, set[str]]:
    """Find keyword phrases claimed by more than one owner (category).

    Returns:
        Each ambiguous normalized phrase mapped to the names of the owners that list it.
    """
    owners: dict[KeywordPhrase, set[str]] = defaultdict(set)
    for owner, keywords in keywords_by_owner.items():
        for keyword in keywords:
            phrase = keyword_words(keyword)
            if phrase:
                owners[phrase].add(owner)
    return {phrase: names for phrase, names in owners.items() if len(names) > 1}


@dataclass(frozen=True)
class KeywordMatch:
    category_uuid: UUID
    keyword: str


@dataclass(frozen=True)
class _Rule:
    phrase: KeywordPhrase
    category_uuid: UUID


class CategoryKeywordMatcher:
    """Matches product names against every category's keyword phrases. Build once per category set."""

    def __init__(self, categories: list[Category]) -> None:
        keywords_by_category = {str(category.get_uuid()): category.get_keywords() for category in categories}
        ambiguous = find_keyword_conflicts(keywords_by_category)
        if ambiguous:
            logger.warning(
                "Ignoring %d keyword(s) listed under several categories: %s",
                len(ambiguous),
                sorted(" ".join(phrase) for phrase in ambiguous),
            )
        rules: dict[KeywordPhrase, _Rule] = {}
        for category in categories:
            for keyword in category.get_keywords():
                phrase = keyword_words(keyword)
                if phrase and phrase not in ambiguous:
                    rules[phrase] = _Rule(phrase=phrase, category_uuid=category.get_uuid())
        self.__rules = list(rules.values())

    def match(self, product_name: str) -> KeywordMatch | None:
        """Return the most specific keyword match in the product's noun phrase, if any.

        Returns:
            The winning category and keyword, or ``None`` when no keyword matches.
        """
        words = keyword_words(product_noun_phrase(product_name))
        best: tuple[tuple[int, int, int], _Rule] | None = None
        for rule in self.__rules:
            position = _find_phrase(rule.phrase, words)
            if position is None:
                continue
            # Higher is better: more words, then earlier position, then longer keyword text.
            rank = (len(rule.phrase), -position, sum(len(word) for word in rule.phrase))
            if best is None or rank > best[0]:
                best = (rank, rule)
        if best is None:
            return None
        rule = best[1]
        return KeywordMatch(category_uuid=rule.category_uuid, keyword=" ".join(rule.phrase))


def _find_phrase(phrase: KeywordPhrase, words: KeywordPhrase) -> int | None:
    """Return the index where ``phrase`` first occurs in ``words``, or ``None``.

    Returns:
        The starting word index of the first occurrence.
    """
    for start in range(len(words) - len(phrase) + 1):
        if all(_word_matches(keyword, word) for keyword, word in zip(phrase, words[start:], strict=False)):
            return start
    return None


def _word_matches(keyword: str, word: str) -> bool:
    if len(keyword) >= _MIN_STEM_LENGTH:
        return word.startswith(keyword)
    return word == keyword
