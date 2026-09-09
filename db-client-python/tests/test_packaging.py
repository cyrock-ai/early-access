"""Guards the packaging trap: generated files are gitignored, and hatchling honours that.

Without an explicit ``artifacts`` entry the wheel builds **successfully** and is unusable - no
protobuf modules, no version - which is the worst shape a packaging bug can take, because nothing
fails until a user installs it. Building a wheel here would be slow, so this asserts the two lists
agree instead: everything the package ignores must be something the wheel puts back.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

# tomllib is 3.11+, and this package supports 3.10. Rather than take a `tomli` dependency for one
# test, the guard sits out the oldest interpreter; CI runs it on the newer leg of the matrix.
if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - exercised only on the 3.10 leg
    tomllib = None  # type: ignore[assignment]

CLIENT_ROOT = Path(__file__).resolve().parents[1]
GITIGNORE   = CLIENT_ROOT / ".gitignore"
PYPROJECT   = CLIENT_ROOT / "pyproject.toml"

pytestmark = [
    pytest.mark.skipif(
        not GITIGNORE.is_file() or not PYPROJECT.is_file(),
        reason="running from an installed package rather than a source checkout",
    ),
    pytest.mark.skipif(tomllib is None, reason="tomllib needs Python 3.11; covered on the newer CI leg"),
]


def _ignored_package_paths() -> set[str]:
    """The gitignore entries that point inside the package - the ones a wheel would lose."""
    entries = set()
    for raw in GITIGNORE.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.lstrip("/").startswith("src/cyrock_db"):
            entries.add(line.lstrip("/"))
    return entries


def _config() -> dict[str, Any]:
    assert tomllib is not None  # noqa: S101 - guaranteed by the module-level skip
    return tomllib.loads(PYPROJECT.read_text())


def _wheel_artifacts() -> set[str]:
    return set(_config()["tool"]["hatch"]["build"]["targets"]["wheel"].get("artifacts", []))


def test_everyIgnoredPackageFile_isRestoredAsAWheelArtifact() -> None:
    missing = _ignored_package_paths() - _wheel_artifacts()
    assert not missing, (
        "These paths are gitignored inside the package but not listed under\n"
        "[tool.hatch.build.targets.wheel] artifacts, so the wheel would ship without them:\n  "
        + "\n  ".join(sorted(missing))
    )


def test_theArtifactList_isNotStale() -> None:
    """An artifact entry for a path nothing ignores is dead weight, and hides that it is."""
    extra = _wheel_artifacts() - _ignored_package_paths()
    assert not extra, (
        "Listed as wheel artifacts but not gitignored, so the entry does nothing:\n  "
        + "\n  ".join(sorted(extra))
    )


def test_theVersionIsDynamic_soItCannotBeHardcodedBackIn() -> None:
    config = _config()
    assert "version" in config["project"].get("dynamic", []), (
        "the version is derived from the reactor's pom.xml; a static version here would drift"
    )
    assert config["tool"]["hatch"]["version"]["path"] == "src/cyrock_db/_version.py"
