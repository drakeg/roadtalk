FORBIDDEN_PROVIDER_TERMS = {
    "google_maps_api_key",
    "mapbox_access_token",
    "reservation_provider_api_key",
    "campground_provider_api_key",
}

FORBIDDEN_PRIVACY_FIELDS = {
    "campsite_id",
    "campsite_number",
    "occupancy_count",
    "member_ids",
    "arrival_at",
    "departure_at",
    "visit_history",
}


def test_d09_prohibited_contract_fields_cover_privacy_evidence_boundary() -> None:
    from app.campgrounds.contracts import PROHIBITED_CAMPGROUND_FIELDS

    assert FORBIDDEN_PRIVACY_FIELDS <= PROHIBITED_CAMPGROUND_FIELDS


def test_d09_runtime_has_no_external_campground_provider_credentials() -> None:
    from pathlib import Path

    app_root = Path(__file__).parents[1] / "app"
    runtime = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in app_root.rglob("*.py")
        if path.is_file()
    )
    for forbidden in FORBIDDEN_PROVIDER_TERMS:
        assert forbidden not in runtime


def test_d09_locked_targets_exist_before_named_run() -> None:
    from pathlib import Path

    targets = (
        Path(__file__).parents[2] / "docs" / "evidence" / "sprint-10-d09-targets.md"
    ).read_text(encoding="utf-8")
    assert "100 accounts" in targets
    assert "25 accounts with valid current campground context" in targets
    assert "10 campground communication publishers" in targets
    assert "search p95: <= 500 ms" in targets
    assert "context derivation p95: <= 750 ms" in targets
    assert "authorization composition p95: <= 1500 ms" in targets
