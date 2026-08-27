from app.presence.policy import PresencePoint, aggregate_presence, privacy_cell_center


def test_conflicting_cells_for_one_account_fail_closed() -> None:
    first_latitude, first_longitude = privacy_cell_center(0, 0)
    second_latitude, second_longitude = privacy_cell_center(2, 0)
    points = [
        PresencePoint(
            account_key="conflicted",
            latitude=first_latitude,
            longitude=first_longitude,
        ),
        PresencePoint(
            account_key="conflicted",
            latitude=second_latitude,
            longitude=second_longitude,
        ),
        PresencePoint(
            account_key="first-a",
            latitude=first_latitude,
            longitude=first_longitude,
        ),
        PresencePoint(
            account_key="first-b",
            latitude=first_latitude,
            longitude=first_longitude,
        ),
    ]

    assert aggregate_presence(points) == ()
