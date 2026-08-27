import math

import pytest
from pydantic import ValidationError

from app.presence.policy import (
    PRESENCE_CELL_SIZE_M,
    PRESENCE_MAX_VISIBLE_CELLS,
    PresencePoint,
    aggregate_presence,
    density_bucket,
    privacy_cell_center,
    privacy_cell_index,
)
from app.presence.schemas import NearbyPresenceQuery, NearbyPresenceResponse, PresenceCellResponse


def points_in_same_cell(count: int) -> list[PresencePoint]:
    return [
        PresencePoint(
            account_key=f"account-{index}",
            latitude=40.0 + index * 0.00001,
            longitude=-75.0 + index * 0.00001,
        )
        for index in range(count)
    ]


def test_query_contract_rejects_client_selectors() -> None:
    assert NearbyPresenceQuery.model_validate({}) == NearbyPresenceQuery()

    for forbidden in (
        "account_id",
        "device_id",
        "latitude",
        "longitude",
        "radius_m",
        "cell_id",
        "route",
        "provider",
        "audience",
    ):
        with pytest.raises(ValidationError):
            NearbyPresenceQuery.model_validate({forbidden: "synthetic"})


def test_response_contract_exposes_only_coarse_presence() -> None:
    cell = PresenceCellResponse(
        approximate_latitude=40.0,
        approximate_longitude=-75.0,
        density="few",
    )
    response = NearbyPresenceResponse(expires_at="2026-08-27T04:00:00Z", cells=(cell,))
    encoded = response.model_dump()

    assert encoded["privacy_min_accounts"] == 3
    assert encoded["policy_version"] == "presence-v1"
    assert encoded["cells"][0]["cell_size_m"] == 2000
    assert set(encoded["cells"][0]) == {
        "approximate_latitude",
        "approximate_longitude",
        "cell_size_m",
        "density",
    }
    for forbidden in (
        "account_id",
        "device_id",
        "callsign",
        "exact_distance",
        "bearing",
        "heading",
        "speed",
        "corridor",
        "direction",
        "route",
        "history",
        "count",
    ):
        assert forbidden not in str(encoded).lower()


def test_one_or_two_accounts_are_suppressed() -> None:
    assert aggregate_presence(points_in_same_cell(1)) == ()
    assert aggregate_presence(points_in_same_cell(2)) == ()


def test_three_distinct_accounts_make_one_coarse_cell() -> None:
    cells = aggregate_presence(points_in_same_cell(3))

    assert len(cells) == 1
    assert cells[0].density == "few"
    assert cells[0].account_count == 3
    assert not math.isclose(cells[0].approximate_latitude, 40.0, abs_tol=1e-6)
    assert not math.isclose(cells[0].approximate_longitude, -75.0, abs_tol=1e-6)


def test_duplicate_account_does_not_satisfy_minimum_anonymity() -> None:
    points = [
        PresencePoint(account_key="same", latitude=40.0, longitude=-75.0),
        PresencePoint(account_key="same", latitude=40.0001, longitude=-75.0001),
        PresencePoint(account_key="other", latitude=40.0002, longitude=-75.0002),
    ]

    assert aggregate_presence(points) == ()


def test_density_is_bucketed_instead_of_exposing_exact_count() -> None:
    assert density_bucket(3) == "few"
    assert density_bucket(5) == "few"
    assert density_bucket(6) == "several"
    assert density_bucket(10) == "several"
    assert density_bucket(11) == "many"

    with pytest.raises(ValueError, match="suppressed"):
        density_bucket(2)


def test_cell_index_and_center_are_deterministic() -> None:
    cell = privacy_cell_index(40.0, -75.0)
    center = privacy_cell_center(*cell)

    assert cell == privacy_cell_index(40.0, -75.0)
    assert center == privacy_cell_center(*cell)
    assert PRESENCE_CELL_SIZE_M == 2_000
    assert -85.051129 <= center[0] <= 85.051129
    assert -180 <= center[1] <= 180


def test_invalid_coordinates_fail_closed() -> None:
    for latitude, longitude in (
        (math.nan, -75.0),
        (91.0, -75.0),
        (40.0, math.inf),
        (40.0, -181.0),
    ):
        with pytest.raises(ValueError):
            privacy_cell_index(latitude, longitude)


def test_visible_cells_are_bounded() -> None:
    points: list[PresencePoint] = []
    for cell_index in range(PRESENCE_MAX_VISIBLE_CELLS + 5):
        longitude = -170.0 + cell_index * 1.0
        for account_index in range(3):
            points.append(
                PresencePoint(
                    account_key=f"{cell_index}-{account_index}",
                    latitude=0.0,
                    longitude=longitude,
                )
            )

    assert len(aggregate_presence(points)) == PRESENCE_MAX_VISIBLE_CELLS
