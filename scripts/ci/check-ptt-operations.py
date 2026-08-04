#!/usr/bin/env python3
"""Fail CI when Sprint 4 PTT operations or cost evidence loses a hard control."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    print(f"PTT operations gate: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        fail(f"required file is missing: {path}")
    return target.read_text(encoding="utf-8")


def require_all(path: str, phrases: tuple[str, ...]) -> None:
    content = " ".join(read(path).lower().split())
    for phrase in phrases:
        if " ".join(phrase.lower().split()) not in content:
            fail(f"{path} is missing required control {phrase!r}")


runbook = "docs/runbooks/ptt-operations.md"
require_all(
    runbook,
    (
        "current and incremental monthly cost: **$0 aws + $0 livekit**",
        "3,000 webrtc participant-minutes",
        "10 gb downstream transfer",
        "25 concurrent participants",
        "$10 total incremental cost",
        "about $4–$6 in an active test month",
        "crossing a hard stop requires immediate pause",
        "must never attach a payment method",
        "alerts, not automatic shutdown controls",
        "revoke the superseded key",
        "run the reviewed terraform destroy",
        "re-run the disabled plan and require zero resources",
        "stopping the ec2 instance alone is not a $0 state",
        "does **not** authorize activation",
    ),
)

evidence = "docs/evidence/sprint-4/README.md"
require_all(
    evidence,
    (
        "current and incremental cost: **$0/month**",
        "live-provider and physical-device status: **not performed**",
        "3,000 participant-minutes",
        "10 gb downstream transfer",
        "25 concurrent participants",
        "$10 incremental monthly cost",
        "does **not** prove",
    ),
)

device_template = "docs/evidence/sprint-4/physical-device-media-test-template.md"
require_all(
    device_template,
    (
        "status: not run",
        "maximum projected incremental cost",
        "participant-minutes before / after",
        "downstream gb before / after",
        "peak concurrent participants",
        "any hard stop reached and containment time",
        "aws stack destroyed if used",
        "no sensitive value or audio entered retained evidence",
    ),
)

cloud_template = "docs/evidence/sprint-4/scheduled-cloud-test-record-template.md"
require_all(
    cloud_template,
    (
        "status: not run",
        "pre-cost estimate",
        "maximum estimate is at or below $10",
        "monthly_budget_usd = 10",
        "alerts are understood not to be automatic shutdown",
        "mandatory stop and destroy record",
        "post-destroy enabled plan result",
        "independent ec2/ebs/snapshot/ipv4/ecr/s3/cloudwatch/sns/budget/ssm inventory",
        "delayed billing/usage recheck",
    ),
)


def terraform_number_default(path: str, variable: str) -> int:
    content = read(path)
    block = re.search(
        rf'variable\s+"{re.escape(variable)}"\s*\{{(?P<body>.*?)\n\}}',
        content,
        re.DOTALL,
    )
    if block is None:
        fail(f"{path} does not declare {variable}")
    default = re.search(r"(?m)^\s*default\s*=\s*(\d+)\s*$", block.group("body"))
    if default is None:
        fail(f"{path} does not give {variable} a numeric default")
    return int(default.group(1))


for terraform_path in (
    "infrastructure/environments/field-test/variables.tf",
    "infrastructure/modules/monitoring/variables.tf",
):
    budget = terraform_number_default(terraform_path, "monthly_budget_usd")
    if budget != 10:
        fail(f"{terraform_path} monthly budget default must be exactly $10, found ${budget}")
    if "var.monthly_budget_usd <= 10" not in read(terraform_path):
        fail(f"{terraform_path} does not reject a budget above $10")

tfvars = read("infrastructure/environments/field-test/terraform.tfvars.example")
if not re.search(r"(?m)^enable_field_test\s*=\s*false\s*$", tfvars):
    fail("field-test example must remain disabled")
if not re.search(r"(?m)^enable_monitoring\s*=\s*false\s*$", tfvars):
    fail("field-test monitoring example must remain disabled")
if not re.search(r"(?m)^monthly_budget_usd\s*=\s*10\s*$", tfvars):
    fail("field-test example budget must be exactly $10")

field_test_main = read("infrastructure/environments/field-test/main.tf")
for condition in (
    "var.monthly_budget_usd > 0",
    "var.monthly_budget_usd <= 10",
):
    if condition not in field_test_main:
        fail(f"enabled field-test validation is missing {condition!r}")

workflow = read(".github/workflows/ci.yml")
if "python scripts/ci/check-ptt-operations.py" not in workflow:
    fail("CI does not enforce the Sprint 4 PTT operations gate")

print("PTT operations gate: passed")
