"""Holds the Python client's operation signatures to the Java reference client's.

``client-java`` is the reference implementation, and ``client-java/src/test/resources/operation-signatures.tsv``
is a generated table of each operation's name and the order of its parameters. ``OperationSignatureContractTest``
holds the Java interface to that file; this holds the Python facade to it - so an operation that takes the same
parameters in a different order, or under different names, fails here. That is the ``executeCollection`` /
``execute_collection`` swap the issue's comment describes: invisible to ``test_parity.py`` (which compares the two
Python facades to each other, and both were wrong the same way) and to ``test_types_mirror_java.py`` (enums only),
because every call site passed the arguments by keyword.

Skipped when the reactor is not beside us, which is the case in a published copy of ``client-python`` and in a
wheel - the same treatment the other cross-language fixtures get.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from cyrock_db.client import CyrockDbClient

FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "client-java" / "src" / "test" / "resources" / "operation-signatures.tsv"
)

pytestmark = pytest.mark.skipif(
    not FIXTURE.is_file(),
    reason="the client-java module is not beside this checkout; nothing to compare against",
)

# Operations whose Python signature deliberately differs from the Java one, each with a stated reason.
# Anything not here must match exactly. Adding to it should take an argument, not a keystroke - each entry
# is a divergence the corpus can no longer catch, so it must be one that is intended and cannot be removed.
DELIBERATELY_DIFFERENT: dict[str, str] = {
    "upsert": (
        "Java names the parameter 'id'; Python names it 'document_id'. 'id' shadows the Python builtin, and "
        "every other operation here already says 'document_id' (get_by_id, delete), so the Python facade is "
        "consistent with itself at the cost of this one name differing from Java."
    ),
    "put_community_summaries": (
        "Java names the parameter 'requests'; Python names it 'requests_'. The plain name shadows the "
        "cyrock_db._proto_requests module the method's own body imports as 'requests', so the trailing "
        "underscore is forced by the implementation, not a stylistic choice."
    ),
}


def _rows() -> list[tuple[str, list[str]]]:
    # Evaluated at collection time, before the skip mark applies, so a published copy with no reactor beside
    # it must return nothing rather than fail to read a missing file.
    if not FIXTURE.is_file():
        return []
    rows = []
    for line in FIXTURE.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        operation, _, params = stripped.partition("\t")
        rows.append((operation, [p for p in params.split(",") if p]))
    return rows


def _python_parameters(operation: str) -> list[str] | None:
    member = inspect.getattr_static(CyrockDbClient, operation, None)
    if not callable(member):
        return None
    return [name for name in inspect.signature(member).parameters if name != "self"]


@pytest.mark.parametrize(("operation", "java_params"), _rows(), ids=[row[0] for row in _rows()])
def test_everyJavaOperation_hasAPythonTwin_takingTheSameParametersInOrder(
    operation: str, java_params: list[str]
) -> None:
    if operation in DELIBERATELY_DIFFERENT:
        pytest.skip(DELIBERATELY_DIFFERENT[operation])

    python_params = _python_parameters(operation)
    assert python_params is not None, (
        f"CyrockDbClient (Python) has no operation '{operation}', which client-java offers. Add it, or - with "
        f"a reason - to DELIBERATELY_DIFFERENT."
    )
    assert python_params == java_params, (
        f"'{operation}' takes different parameters in Python than in Java.\n"
        f"  Java:   {java_params}\n"
        f"  Python: {python_params}\n"
        "Same operations, same names, same order. Fix the Python signature, or - with a reason - add it to "
        "DELIBERATELY_DIFFERENT."
    )


def test_theFixture_isNotTrivial() -> None:
    """A corpus that failed to load would make every parametrized case vacuously pass."""
    assert len(_rows()) >= 40, "operation-signatures.tsv looks empty or truncated"


def test_theAllowList_namesOnlyOperationsInTheCorpus() -> None:
    """A stale exemption would silently excuse an operation that is back to matching - or never existed."""
    operations = {operation for operation, _ in _rows()}
    stale = [name for name in DELIBERATELY_DIFFERENT if name not in operations]
    assert not stale, f"DELIBERATELY_DIFFERENT names operations not in the corpus: {stale}"
