"""Validate every profile.json in the repo using the script's own validator.

Run from the repo root:  python tools/validate_profiles.py

This reuses src/TrackMagnet/config.py — the exact code that runs inside Live —
so CI and the runtime can never disagree about what a valid profile is.
Exits non-zero if any profile has problems.
"""

import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from TrackMagnet import config  # noqa: E402


def main():
    profiles = sorted(REPO_ROOT.glob("src/TrackMagnet/profile.json")) + sorted(
        REPO_ROOT.glob("profiles/*/profile.json")
    )
    if not profiles:
        print("ERROR: no profile.json files found — is the repo layout intact?")
        return 1

    failures = 0
    for path in profiles:
        relative = path.relative_to(REPO_ROOT)
        profile = config.load_profile(str(path))
        if profile.problems:
            failures += 1
            print(f"FAIL {relative}")
            for problem in profile.problems:
                print(f"     - {problem}")
        else:
            controls = "; ".join(control.describe() for control in profile.controls)
            print(f"OK   {relative}  ({profile.name}: {controls})")

    if failures:
        print(f"\n{failures} profile(s) failed validation.")
        return 1
    print(f"\nAll {len(profiles)} profile(s) valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
