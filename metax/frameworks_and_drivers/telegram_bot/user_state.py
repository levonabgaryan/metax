"""Per-user bot session state: language, retailer filter, and the view the user is looking at.

Kept in process memory: it is lost on restart and not shared between bot replicas, which is fine
for a single long-polling bot whose state is pure convenience (everything falls back to defaults).
"""

from __future__ import annotations

from dataclasses import dataclass

from metax.frameworks_and_drivers.telegram_bot.localization import DEFAULT_LANGUAGE, normalize_language


@dataclass
class UserSession:
    language: str = DEFAULT_LANGUAGE
    retailer_uuid: str | None = None
    # The user's active result view, so changing the retailer filter re-applies to whatever they are
    # looking at. A user is either searching or browsing a category, never both: entering one clears
    # the other.
    last_query: str | None = None
    last_category_uuid: str | None = None

    def set_language(self, language_code: str) -> None:
        self.language = normalize_language(language_code)

    def enter_search(self, query: str) -> None:
        self.last_query = query
        self.last_category_uuid = None

    def enter_category(self, category_uuid: str) -> None:
        self.last_category_uuid = category_uuid
        self.last_query = None


_SESSIONS: dict[int, UserSession] = {}


def session_for(user_id: int | None) -> UserSession:
    """Return the user's session, creating it on first contact.

    Updates without a sender (``user_id is None``) get a throwaway default session.

    Returns:
        The (mutable) session for ``user_id``.
    """
    if user_id is None:
        return UserSession()
    return _SESSIONS.setdefault(user_id, UserSession())
