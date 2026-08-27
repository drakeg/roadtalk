from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Literal

WEB_MERCATOR_MAX_LATITUDE = 85.05112878
WEB_MERCATOR_RADIUS_M = 6_378_137.0
PRESENCE_CELL_SIZE_M = 2_000
PRESENCE_MIN_VISIBLE_ACCOUNTS = 3
PRESENCE_MAX_VISIBLE_CELLS = 32

DensityBucket = Literal["few", "several", "many"]


@dataclass(frozen=True, slots=True)
class PresencePoint:
    account_key: str
    latitude: float
    longitude: float


@dataclass(frozen=True, slots=True)
class PresenceCell:
    approximate_latitude: float
    approximate_longitude: float
    density: DensityBucket
    account_count: int


def density_bucket(account_count: int) -> DensityBucket:
    if account_count < PRESENCE_MIN_VISIBLE_ACCOUNTS:
        raise ValueError("suppressed presence cannot be assigned a density bucket")
    if account_count <= 5:
        return "few"
    if account_count <= 10:
        return "several"
    return "many"


def _normalize_longitude(longitude: float) -> float:
    if not math.isfinite(longitude):
        raise ValueError("longitude must be finite")
    if longitude < -180 or longitude > 180:
        raise ValueError("longitude must be between -180 and 180")
    return longitude


def _clamp_latitude(latitude: float) -> float:
    if not math.isfinite(latitude):
        raise ValueError("latitude must be finite")
    if latitude < -90 or latitude > 90:
        raise ValueError("latitude must be between -90 and 90")
    return max(-WEB_MERCATOR_MAX_LATITUDE, min(WEB_MERCATOR_MAX_LATITUDE, latitude))


def _to_mercator(latitude: float, longitude: float) -> tuple[float, float]:
    latitude = _clamp_latitude(latitude)
    longitude = _normalize_longitude(longitude)
    x = WEB_MERCATOR_RADIUS_M * math.radians(longitude)
    y = WEB_MERCATOR_RADIUS_M * math.log(math.tan(math.pi / 4 + math.radians(latitude) / 2))
    return x, y


def _from_mercator(x: float, y: float) -> tuple[float, float]:
    longitude = math.degrees(x / WEB_MERCATOR_RADIUS_M)
    latitude = math.degrees(2 * math.atan(math.exp(y / WEB_MERCATOR_RADIUS_M)) - math.pi / 2)
    return latitude, longitude


def privacy_cell_index(latitude: float, longitude: float) -> tuple[int, int]:
    x, y = _to_mercator(latitude, longitude)
    return math.floor(x / PRESENCE_CELL_SIZE_M), math.floor(y / PRESENCE_CELL_SIZE_M)


def privacy_cell_center(cell_x: int, cell_y: int) -> tuple[float, float]:
    x = (cell_x + 0.5) * PRESENCE_CELL_SIZE_M
    y = (cell_y + 0.5) * PRESENCE_CELL_SIZE_M
    return _from_mercator(x, y)


def aggregate_presence(points: Iterable[PresencePoint]) -> tuple[PresenceCell, ...]:
    """Aggregate current candidates without exposing sparse or exact-account locations."""

    account_cells: dict[str, tuple[int, int] | None] = {}
    for point in points:
        cell = privacy_cell_index(point.latitude, point.longitude)
        if point.account_key not in account_cells:
            account_cells[point.account_key] = cell
        elif account_cells[point.account_key] != cell:
            account_cells[point.account_key] = None

    cell_accounts: dict[tuple[int, int], set[str]] = {}
    for account_key, cell in account_cells.items():
        if cell is not None:
            cell_accounts.setdefault(cell, set()).add(account_key)

    visible: list[tuple[tuple[int, int], set[str]]] = [
        (cell, accounts)
        for cell, accounts in cell_accounts.items()
        if len(accounts) >= PRESENCE_MIN_VISIBLE_ACCOUNTS
    ]
    visible.sort(key=lambda item: (-len(item[1]), item[0][1], item[0][0]))

    result: list[PresenceCell] = []
    for (cell_x, cell_y), accounts in visible[:PRESENCE_MAX_VISIBLE_CELLS]:
        latitude, longitude = privacy_cell_center(cell_x, cell_y)
        result.append(
            PresenceCell(
                approximate_latitude=latitude,
                approximate_longitude=longitude,
                density=density_bucket(len(accounts)),
                account_count=len(accounts),
            )
        )
    return tuple(result)
