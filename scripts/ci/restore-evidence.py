#!/usr/bin/env python3
"""Generate or validate a Sprint 16 isolated restore evidence record.

This tool is metadata-only. It does not connect to AWS, databases, backups, or production.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def parse_ts(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return parsed


def validate(record: dict) -> None:
    required = (
        "environment",
        "recovery_point_id",
        "recovery_point_timestamp",
        "restore_start_timestamp",
        "restore_complete_timestamp",
        "integrity_check_passed",
        "schema_validation_passed",
        "application_smoke_passed",
        "isolated_target",
        "production_overwrite_performed",
    )
    for key in required:
        if key not in record:
            raise ValueError(f"missing evidence field: {key}")

    if record["environment"] != "isolated-restore-test":
        raise ValueError("restore evidence must target isolated-restore-test")
    if record["isolated_target"] is not True:
        raise ValueError("restore target must be isolated")
    if record["production_overwrite_performed"] is not False:
        raise ValueError("production overwrite must remain false")
    for key in ("integrity_check_passed", "schema_validation_passed", "application_smoke_passed"):
        if record[key] is not True:
            raise ValueError(f"{key} must be true")

    recovery = parse_ts(record["recovery_point_timestamp"])
    start = parse_ts(record["restore_start_timestamp"])
    complete = parse_ts(record["restore_complete_timestamp"])
    if not recovery <= start <= complete:
        raise ValueError("timestamps must satisfy recovery_point <= restore_start <= restore_complete")

    measured_rpo = (start - recovery).total_seconds() / 60
    measured_rto = (complete - start).total_seconds() / 60
    record["measured_rpo_minutes"] = round(measured_rpo, 2)
    record["measured_rto_minutes"] = round(measured_rto, 2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path)
    parser.add_argument("--write-normalized", action="store_true")
    args = parser.parse_args()

    record = json.loads(args.record.read_text())
    validate(record)
    if args.write_normalized:
        args.record.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({
        "recovery_point_id": record["recovery_point_id"],
        "measured_rpo_minutes": record["measured_rpo_minutes"],
        "measured_rto_minutes": record["measured_rto_minutes"],
        "live_production_evidence": False,
    }))


if __name__ == "__main__":
    main()
