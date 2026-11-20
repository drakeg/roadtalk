#!/usr/bin/env python3
"""Validate repository-level Mad Mallard standards adopted by RoadTalk."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
REQUIRED = ("AGENTS.md", "CONTRIBUTING.md", "SPRINTS.md", "BACKLOG.md", "RELEASES.md", "SECURITY.md")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    for name in REQUIRED:
        require((ROOT / name).is_file(), f"missing repository standard: {name}")

    text = README.read_text()
    require(text.startswith("# RoadTalk\n"), "README must retain RoadTalk H1")
    start = text.find("<!-- madmallard-badges:start -->")
    end = text.find("<!-- madmallard-badges:end -->")
    require(0 < start < end, "README badge block missing or malformed")
    require(start < text.find("RoadTalk is"), "badge block must be immediately below project title")

    badge_block = text[start:end]
    expected = (
        "actions/workflows/ci.yml/badge.svg",
        "label=tests",
        "label=security",
        "Python-3.14",
        "FastAPI-0.165.x",
        "React_Native-0.86.3",
        "Expo_SDK-57",
        "PostgreSQL-17",
        "PostGIS-3.5",
        "Redis-8",
        "Terraform-1.17.2",
        "github/issues/drakeg/roadtalk",
        "github/issues-pr/drakeg/roadtalk",
    )
    for token in expected:
        require(token in badge_block, f"missing verified README badge token: {token}")

    # RoadTalk currently has no repository LICENSE file or published GitHub release.
    require("github/license/drakeg/roadtalk" not in badge_block, "license badge requires repository LICENSE")
    require("github/v/release/drakeg/roadtalk" not in badge_block, "release badge requires a published release")

    agents = (ROOT / "AGENTS.md").read_text()
    require("madmallard-repository-standards" in agents, "AGENTS must reference centralized standards")
    require("badge" in agents.lower(), "AGENTS must document badge maintenance")

    backlog = (ROOT / "BACKLOG.md").read_text()
    require("SMB" in backlog and "paid pilot" in backlog, "BACKLOG must retain commercialization priorities")

    print("Repository standards validation: passed")


if __name__ == "__main__":
    main()
