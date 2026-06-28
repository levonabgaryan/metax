"""Armenian → Latin phonetic transliteration for cross-script search.

Product names are Armenian (``կարագ``), but users often type the Latin phonetic form (``karag``).
We store a transliterated copy of each name (``name_translit``) and transliterate the query the same
way, so a Latin query matches the Armenian name lexically. The mapping is deliberately phonetic and
lossy (e.g. both ``տ`` and ``թ`` → ``t``): several Armenian letters collapsing onto one Latin letter
widens recall, which is what we want for fuzzy phonetic matching.

Latin (and any other non-Armenian) characters pass through unchanged, so the function doubles as a
no-op normaliser for already-Latin queries and brand names.
"""

from __future__ import annotations

# Multi-codepoint sequences, replaced before the per-character map (order matters: longest first).
_DIGRAPHS: tuple[tuple[str, str], ...] = (
    ("ու", "u"),
    ("և", "ev"),
)

_CHAR_MAP: dict[str, str] = {
    "ա": "a", "բ": "b", "գ": "g", "դ": "d", "ե": "e", "զ": "z", "է": "e", "ը": "e",
    "թ": "t", "ժ": "zh", "ի": "i", "լ": "l", "խ": "kh", "ծ": "ts", "կ": "k", "հ": "h",
    "ձ": "dz", "ղ": "gh", "ճ": "ch", "մ": "m", "յ": "y", "ն": "n", "շ": "sh", "ո": "o",
    "չ": "ch", "պ": "p", "ջ": "j", "ռ": "r", "ս": "s", "վ": "v", "տ": "t", "ր": "r",
    "ց": "ts", "ւ": "v", "փ": "p", "ք": "q", "օ": "o", "ֆ": "f",
}


def transliterate_armenian_to_latin(text: str) -> str:
    """Return the Latin phonetic transliteration of ``text``.

    Armenian letters are mapped to their common Latin equivalents; everything else (Latin letters,
    digits, spaces, punctuation) is left as-is. The result is lower-cased so it is a stable search
    key regardless of the source casing.

    Returns:
        The transliterated, lower-cased string.
    """
    lowered = text.lower()
    for source, target in _DIGRAPHS:
        lowered = lowered.replace(source, target)
    return "".join(_CHAR_MAP.get(char, char) for char in lowered)
