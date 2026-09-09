"""Classifies a CyQL statement well enough to route it, without parsing it.

``execute``, ``execute_collection``, ``query`` and ``query_collection`` decide client-side whether a
statement belongs to the project (control plane) or to a graph or collection (data plane). The Java
client answers that by parsing: ``Cyql.parseStatement(...).statementClass()``. That parser is sixty
files and is not ported here.

It does not need to be. A statement's class is decided by its leading keyword phrase, and the routing
decision is binary - project-scoped DDL, or everything else - so recognising the eight project-scoped
openings is enough. Everything unrecognised routes to the resource, which is where a plain ``MATCH``,
``INSERT``, ``LOAD CSV`` or ``ALTER`` belongs anyway, and where an unparseable statement should go so
that the server produces the syntax error rather than this module guessing at one.

**``CREATE`` is the trap.** ``CREATE GRAPH g`` is project-scoped DDL; ``CREATE (n:Label)`` is a data
write. The same holds for ``DROP``. So the classifier reads two words, never one, and a bare
``CREATE`` falls through to the data plane - which is correct, and is why the recognised set is
written as pairs rather than as a set of first words.

Drift is guarded by ``tests/test_cyql_routing.py``, which reads a fixture the Java build generates
from the real parser. A grammar change that reclassifies a statement fails the Python build too.
"""

from __future__ import annotations

import re

from .types import StatementClass

__all__ = ["is_project_scoped", "statement_class"]

# The (first, second) keyword pairs whose statements execute on the platform server, which owns the
# resource definitions. Everything else executes on the data server holding the resource's lease.
_PROJECT_SCOPED: frozenset[tuple[str, str]] = frozenset({
    ("CREATE",   "GRAPH"),
    ("CREATE",   "COLLECTION"),
    ("DROP",     "GRAPH"),
    ("DROP",     "COLLECTION"),
    ("SHOW",     "GRAPHS"),
    ("SHOW",     "COLLECTIONS"),
    ("DESCRIBE", "GRAPH"),
    ("DESCRIBE", "COLLECTION"),
})

# Leading line and block comments, so a commented statement classifies by its first real keyword.
_COMMENTS = re.compile(r"^\s*(?://[^\n]*\n|/\*.*?\*/|\s)+", re.DOTALL)


def _leading_words(statement: str) -> tuple[str, str]:
    """The first two words, upper-cased. Missing words come back empty rather than raising."""
    if not statement:
        return ("", "")
    stripped = _COMMENTS.sub("", statement, count=1)
    words    = stripped.split(maxsplit=2)
    first    = words[0].upper() if words else ""
    second   = words[1].upper() if len(words) > 1 else ""
    return (first, second)


def is_project_scoped(statement: str) -> bool:
    """Whether this statement executes on the platform server rather than on a resource.

    The only question the routing methods actually ask. Anything unrecognised is not project-scoped.
    """
    return _leading_words(statement) in _PROJECT_SCOPED


def statement_class(statement: str) -> StatementClass | None:
    """The statement's routing class, as far as keywords can tell, or ``None`` if they cannot.

    ``None`` is returned rather than a guess for anything past the project-scoped set and the two
    resource-scoped ``ALTER`` forms: telling ``MATCH ... SET`` (a write) from ``MATCH ... RETURN``
    (a read) needs the parser, and this module deliberately does not have one. Routing never needs
    that distinction - both go to the resource - so :func:`is_project_scoped` is what the client
    calls. This function exists for the drift fixture, which can check what is claimed and skip what
    is not.
    """
    first, second = _leading_words(statement)
    if (first, second) in _PROJECT_SCOPED:
        return StatementClass.PROJECT_SCOPED_DDL
    if first == "ALTER" and second == "GRAPH":
        return StatementClass.GRAPH_SCOPED_DDL
    if first == "ALTER" and second == "COLLECTION":
        return StatementClass.COLLECTION_SCOPED_DDL
    return None
