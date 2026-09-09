"""The keyword classifier, held to the CyQL grammar through a shared fixture.

``cyql/src/test/resources/statement-classes.tsv`` records what the real parser answers for a spread
of statements. ``StatementClassContractTest`` asserts the grammar still agrees with that file; this
asserts the Python classifier does too. So a grammar change that reclassifies a statement fails the
Java build, and updating the fixture then fails this one if the keyword rules have fallen behind -
which is the whole reason the two sides read one file instead of keeping two lists.

The classifier is deliberately partial. It answers PROJECT_SCOPED_DDL, GRAPH_SCOPED_DDL and
COLLECTION_SCOPED_DDL, and returns ``None`` for READ_QUERY and DATA_WRITE, because telling
``MATCH ... RETURN`` from ``MATCH ... SET`` needs the parser. Routing never asks: both go to the
resource. So the fixture check is asymmetric on purpose - where the classifier commits it must be
right, and where it declines it must at least not be project-scoped.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cyrock_db._cyql_routing import is_project_scoped, statement_class
from cyrock_db.types import StatementClass

FIXTURE = (
    Path(__file__).resolve().parents[2] / "cyql" / "src" / "test" / "resources" / "statement-classes.tsv"
)

pytestmark = pytest.mark.skipif(
    not FIXTURE.is_file(),
    reason="the cyql module is not beside this checkout; nothing to check against",
)


def _entries() -> list[tuple[StatementClass, str]]:
    # The skipif above is not enough on its own: parametrize evaluates this at collection time, before
    # any mark is applied, so a published copy with no cyql module beside it would fail to collect
    # rather than skip. Returning nothing leaves pytest an empty parameter set, which it skips.
    if not FIXTURE.is_file():
        return []

    entries = []
    for line in FIXTURE.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        expected, statement = stripped.split("\t", 1)
        entries.append((StatementClass[expected], statement))
    return entries


def _ids() -> list[str]:
    return [statement[:48] for _, statement in _entries()]


@pytest.mark.parametrize(("expected", "statement"), _entries(), ids=_ids())
def test_projectScopedRouting_agreesWithTheGrammar(expected: StatementClass, statement: str) -> None:
    """The one question routing actually asks, checked against every fixture statement."""
    assert is_project_scoped(statement) is (expected is StatementClass.PROJECT_SCOPED_DDL)


@pytest.mark.parametrize(("expected", "statement"), _entries(), ids=_ids())
def test_whereTheClassifierCommits_itAgreesWithTheGrammar(
    expected: StatementClass, statement: str
) -> None:
    """Where it answers at all, the answer must be the grammar's. Declining is allowed."""
    answered = statement_class(statement)
    if answered is not None:
        assert answered is expected


def test_theClassifierDeclinesOnlyWhereTheParserIsNeeded() -> None:
    """It must not quietly stop answering for a class it is supposed to recognise.

    Without this, a regression that made ``statement_class`` return None for everything would leave
    the test above passing on an empty set of assertions.
    """
    declined = {
        expected for expected, statement in _entries() if statement_class(statement) is None
    }
    assert declined <= {StatementClass.READ_QUERY, StatementClass.DATA_WRITE}, (
        f"the classifier stopped recognising {declined - {StatementClass.READ_QUERY, StatementClass.DATA_WRITE}}"
    )


def test_theFixtureCoversTheClassesRoutingDependsOn() -> None:
    covered = {expected for expected, _ in _entries()}
    assert StatementClass.PROJECT_SCOPED_DDL in covered
    assert StatementClass.DATA_WRITE in covered, "the CREATE ambiguity needs a data-write example"
    assert len(_entries()) >= 10


def test_theCreateAmbiguity_isCoveredBothWays() -> None:
    """CREATE GRAPH is project DDL and CREATE (n) is a data write; one keyword cannot tell them apart."""
    creates = [
        (expected, statement) for expected, statement in _entries()
        if statement.upper().startswith("CREATE")
    ]
    classes = {expected for expected, _ in creates}
    assert StatementClass.PROJECT_SCOPED_DDL in classes
    assert StatementClass.DATA_WRITE in classes, (
        "without a bare-CREATE example the fixture cannot catch a classifier that reads one word"
    )
