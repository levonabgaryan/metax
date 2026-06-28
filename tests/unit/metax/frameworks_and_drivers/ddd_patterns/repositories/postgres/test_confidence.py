"""Unit tests for the distance->confidence mapping used by search/category read models."""

from __future__ import annotations

import pytest

from metax.frameworks_and_drivers.ddd_patterns.repositories.postgres.discounted_product_read_model import (
    _confidence_from_distance,
)


@pytest.mark.parametrize(
    ("distance", "expected"),
    [
        (0.0, 1.0),  # identical -> fully confident
        (0.4, 0.6),  # at the strict gate
        (1.0, 0.0),  # orthogonal -> no confidence
        (1.5, 0.0),  # clamped, never negative
        (None, 0.0),  # unknown -> no confidence
    ],
)
def test_confidence_from_distance(distance: float | None, expected: float) -> None:
    assert _confidence_from_distance(distance) == pytest.approx(expected)
