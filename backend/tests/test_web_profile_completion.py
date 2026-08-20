from app.api.identity import DEFAULT_WEB_AVATAR_ID, web_profile_avatar_id


def test_web_callsign_save_assigns_default_avatar_when_missing() -> None:
    assert (
        web_profile_avatar_id(
            platform="web",
            callsign="Road-Runner",
            requested_avatar_id=None,
            existing_avatar_id=None,
        )
        == DEFAULT_WEB_AVATAR_ID
    )


def test_web_callsign_save_preserves_existing_avatar() -> None:
    assert (
        web_profile_avatar_id(
            platform="web",
            callsign="Road-Runner",
            requested_avatar_id=None,
            existing_avatar_id="night-owl",
        )
        is None
    )


def test_mobile_callsign_save_does_not_assign_web_default_avatar() -> None:
    assert (
        web_profile_avatar_id(
            platform="ios",
            callsign="Road-Runner",
            requested_avatar_id=None,
            existing_avatar_id=None,
        )
        is None
    )


def test_explicit_avatar_always_wins() -> None:
    assert (
        web_profile_avatar_id(
            platform="web",
            callsign="Road-Runner",
            requested_avatar_id="pine-trail",
            existing_avatar_id=None,
        )
        == "pine-trail"
    )
