import inspect

from app.campgrounds.context import derive_current_campground_context


def test_derivation_entrypoint_has_no_client_selected_campground_or_audience() -> None:
    parameters = set(inspect.signature(derive_current_campground_context).parameters)
    assert parameters == {"db", "account_id", "location_policy_version", "now"}
    assert "campground_id" not in parameters
    assert "recipient_ids" not in parameters
    assert "audience" not in parameters
    assert "authorization" not in parameters
