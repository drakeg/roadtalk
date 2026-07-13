import uuid

from sqlalchemy import CheckConstraint

from app.db.models import Account, Profile


def test_profile_is_optional_for_existing_accounts() -> None:
    account = Account(id=uuid.uuid4())

    assert account.profile is None


def test_profile_has_one_to_one_account_ownership() -> None:
    account = Account(id=uuid.uuid4())
    profile = Profile(
        account=account,
        normalized_callsign="road-runner",
        display_callsign="Road-Runner",
        avatar_id="classic-radio",
        setup_completed=True,
        version=1,
    )

    assert account.profile is profile
    assert profile.account is account
    assert list(Profile.__table__.primary_key.columns.keys()) == ["account_id"]
    assert next(iter(Profile.__table__.c.account_id.foreign_keys)).ondelete == "CASCADE"


def test_profile_metadata_preserves_incomplete_identity_state() -> None:
    table = Profile.__table__
    check_names = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert table.c.normalized_callsign.nullable
    assert table.c.display_callsign.nullable
    assert table.c.avatar_id.nullable
    assert table.c.setup_completed.nullable is False
    assert table.c.version.nullable is False
    assert {
        "ck_profile_callsign_pair",
        "ck_profile_completed_fields",
        "ck_profile_version_positive",
    } <= check_names


def test_profile_callsign_index_is_unique_and_null_tolerant() -> None:
    callsign_index = next(
        index
        for index in Profile.__table__.indexes
        if index.name == "uq_profile_normalized_callsign"
    )

    assert callsign_index.unique
    assert [column.name for column in callsign_index.columns] == ["normalized_callsign"]
