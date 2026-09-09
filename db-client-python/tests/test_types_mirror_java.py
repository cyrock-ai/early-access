"""Holds the Python enums to the Java ones they mirror.

Several of these cross the wire as strings - ``StatementClass`` and ``StatementType`` are parsed back
by name - so a member added on the Java side and forgotten here is not a cosmetic divergence: it is a
``KeyError`` in ``_proto_converters`` the first time a server sends it. Reading the Java source is
cruder than a shared fixture, but it needs nothing from the Java build and catches the drift at the
only moment anyone is looking.

Skipped when the reactor is not beside us, which is the case in a published copy of ``client-python``
and in a wheel. Nothing here is asserted about the SDK's behaviour, only about its agreement with a
sibling module that a released artifact no longer has.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from cyrock_db.types import (
    Cardinality,
    Direction,
    FusionStrategy,
    MetadataFieldType,
    SimilarityFunction,
    StatementClass,
    StatementType,
)

REPO_ROOT     = Path(__file__).resolve().parents[2]
JAVA_DATA_DIR = REPO_ROOT / "data" / "src" / "main" / "java" / "ai" / "cyrock" / "db" / "data"

pytestmark = pytest.mark.skipif(
    not JAVA_DATA_DIR.is_dir(),
    reason="the reactor's data module is not beside this checkout; nothing to compare against",
)

# An enum constant is a bare identifier at the head of a line inside the enum body, ending in a
# comma, a semicolon, or the closing brace. Deliberately narrow: it must not match a method, a field
# or a switch arm, all of which appear in these files.
_CONSTANT = re.compile(r"^\s{4}([A-Z][A-Z0-9_]*)\s*(?:,|;|$)", re.MULTILINE)


def _java_enum_constants(type_name: str) -> list[str]:
    source = (JAVA_DATA_DIR / f"{type_name}.java").read_text()
    body   = source[source.index("{", source.index(f"enum {type_name}")):]
    return _CONSTANT.findall(body)


@pytest.mark.parametrize(
    ("python_enum", "java_name"),
    [
        (StatementClass,     "StatementClass"),
        (StatementType,      "StatementType"),
        (SimilarityFunction, "SimilarityFunction"),
        (FusionStrategy,     "FusionStrategy"),
        (Direction,          "Direction"),
        (Cardinality,        "Cardinality"),
        (MetadataFieldType,  "MetadataFieldType"),
    ],
)
def test_pythonEnum_comparedToTheJavaEnum_hasTheSameMembers(python_enum: type, java_name: str) -> None:
    java_constants   = _java_enum_constants(java_name)
    python_constants = [member.name for member in python_enum]

    assert java_constants, f"parsed no constants out of {java_name}.java; the parser needs fixing, not the enum"
    assert python_constants == java_constants, (
        f"{python_enum.__name__} has drifted from {java_name}.\n"
        f"  only in Java:   {sorted(set(java_constants) - set(python_constants))}\n"
        f"  only in Python: {sorted(set(python_constants) - set(java_constants))}\n"
        "Order matters too: these cross the wire by name and are read as a list in docs."
    )


def test_everyMemberValue_equalsItsName() -> None:
    """The wire form is the member name, so a value that differs from it is a latent mismatch."""
    for enum_type in (StatementClass, StatementType, SimilarityFunction, FusionStrategy, Direction,
                      Cardinality, MetadataFieldType):
        for member in enum_type:
            assert member.value == member.name, f"{enum_type.__name__}.{member.name} has value {member.value!r}"


def test_packageVersion_matchesTheReactorPom() -> None:
    """The Python and Java artifacts are released together and must not carry different versions."""
    import re

    from cyrock_db._version import __version__

    pom   = (REPO_ROOT / "pom.xml").read_text()
    maven = re.search(r"<version>([^<]+)</version>", pom)
    assert maven is not None

    expected = maven[1].strip()
    if expected.endswith("-SNAPSHOT"):
        expected = expected.removesuffix("-SNAPSHOT") + ".dev0"
    assert __version__ == expected, (
        f"pyproject builds {__version__} but the reactor is at {maven[1].strip()}; "
        "re-run scripts/generate_proto.py"
    )
