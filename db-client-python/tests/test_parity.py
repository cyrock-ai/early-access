"""Holds :class:`AsyncCyrockDbClient` to :class:`CyrockDbClient`.

The counterpart of ``AsyncClientParityTest``. The two facades are written and maintained separately -
that is the deliberate choice, so the synchronous client keeps its own tracebacks and does not pay a
handoff for a call that blocks anyway. The cost of that choice is that they can drift, and drift here
is invisible: a method added to one and forgotten on the other imports, ships, and is noticed only by
whoever needed it.

It fails in both directions on purpose. A synchronous method with no twin is the expected drift; an
asynchronous method with no synchronous counterpart is rarer and just as much a defect - it means the
two are no longer the same API.
"""

from __future__ import annotations

import inspect
from typing import Any

import pytest

from cyrock_db.aio import AsyncCyrockDbClient
from cyrock_db.client import CyrockDbClient

# Synchronous methods with deliberately no asynchronous twin, each for a stated reason. Anything not
# on this list needs one. Adding to it should take an argument, not a keystroke.
DELIBERATELY_SYNCHRONOUS_ONLY = {
    "close": "lifecycle: present on both, but async def close cannot share a signature with def close",
}

# Asynchronous methods with deliberately no synchronous twin.
DELIBERATELY_ASYNCHRONOUS_ONLY = {
    "close": "as above",
}

# Twins that exist on both clients but take different parameters, each for a stated reason. This list
# is separate from the two above because the methods *do* both exist - it is only their shape that
# differs, and saying so is more honest than pretending one of them is absent.
DELIBERATELY_DIFFERENT_SIGNATURES = {
    "watch_graph": (
        "a change stream delivers many events, which no single return value can express. The "
        "blocking client takes a listener because a callback is the only way to deliver without "
        "blocking the caller; the asyncio client returns an async iterator, which is the same idea "
        "with the control inverted and what a Python caller expects. client-java lists watchGraph "
        "and watchCollection on its own omission list for the same underlying reason."
    ),
    "watch_collection": "as watch_graph",
}


def _operations(client_type: type) -> dict[str, inspect.Signature]:
    """The public operations of a client: its own methods, minus dunders and context management."""
    operations = {}
    for name, member in inspect.getmembers(client_type, predicate=inspect.isfunction):
        if name.startswith("_"):
            continue
        operations[name] = inspect.signature(member)
    return operations


def _comparable(signature: inspect.Signature) -> list[tuple[str, Any]]:
    """A signature reduced to what parity is about: parameter names and annotations, minus self."""
    return [
        (name, parameter.annotation)
        for name, parameter in signature.parameters.items()
        if name != "self"
    ]


def test_asyncClient_comparedToTheSyncClient_mirrorsEveryOperation() -> None:
    synchronous  = _operations(CyrockDbClient)
    asynchronous = _operations(AsyncCyrockDbClient)

    missing = [
        name for name in synchronous
        if name not in asynchronous and name not in DELIBERATELY_SYNCHRONOUS_ONLY
    ]
    assert not missing, (
        "AsyncCyrockDbClient is missing a twin for:\n  " + "\n  ".join(missing)
        + "\n\nAdd it, or - with a reason - to DELIBERATELY_SYNCHRONOUS_ONLY."
    )


def test_asyncClient_comparedToTheSyncClient_addsNothingOfItsOwn() -> None:
    synchronous  = _operations(CyrockDbClient)
    asynchronous = _operations(AsyncCyrockDbClient)

    extra = [
        name for name in asynchronous
        if name not in synchronous and name not in DELIBERATELY_ASYNCHRONOUS_ONLY
    ]
    assert not extra, (
        "AsyncCyrockDbClient has operations CyrockDbClient does not:\n  " + "\n  ".join(extra)
        + "\n\nThe two are meant to be the same API. Add the synchronous twin."
    )


def test_everyTwin_takesTheSameParameters() -> None:
    synchronous  = _operations(CyrockDbClient)
    asynchronous = _operations(AsyncCyrockDbClient)

    mismatched = []
    for name, signature in synchronous.items():
        if (
            name not in asynchronous
            or name in DELIBERATELY_SYNCHRONOUS_ONLY
            or name in DELIBERATELY_DIFFERENT_SIGNATURES
        ):
            continue
        if _comparable(signature) != _comparable(asynchronous[name]):
            mismatched.append(
                f"{name}: sync {_comparable(signature)} vs async {_comparable(asynchronous[name])}"
            )
    assert not mismatched, "Twins that do not take the same parameters:\n  " + "\n  ".join(mismatched)


def test_everyAsyncOperation_isACoroutine() -> None:
    wrong = [
        name for name, _ in _operations(AsyncCyrockDbClient).items()
        if not inspect.iscoroutinefunction(getattr(AsyncCyrockDbClient, name))
    ]
    assert not wrong, "Not awaitable:\n  " + "\n  ".join(wrong)


def test_everySyncOperation_isNotACoroutine() -> None:
    wrong = [
        name for name, _ in _operations(CyrockDbClient).items()
        if inspect.iscoroutinefunction(getattr(CyrockDbClient, name))
    ]
    assert not wrong, "Unexpectedly awaitable on the blocking client:\n  " + "\n  ".join(wrong)


@pytest.mark.parametrize(
    "allow_list",
    [DELIBERATELY_SYNCHRONOUS_ONLY, DELIBERATELY_ASYNCHRONOUS_ONLY, DELIBERATELY_DIFFERENT_SIGNATURES],
)
def test_theAllowList_namesOnlyMethodsThatExist(allow_list: dict[str, str]) -> None:
    """Guards the allow-list itself.

    A name that no longer exists would sit there silently excusing a method that does, which is how
    an allow-list stops being one.
    """
    known = set(_operations(CyrockDbClient)) | set(_operations(AsyncCyrockDbClient))
    stale = [name for name in allow_list if name not in known]
    assert not stale, f"DELIBERATELY_* names methods that no longer exist: {stale}"


def test_signatureExemptions_stillHaveBothHalves() -> None:
    """A method exempted from the signature check must still exist on both clients.

    Without this, moving a method to the exemption list and then deleting one half would pass every
    test above - the exemption would quietly become an omission.
    """
    synchronous  = _operations(CyrockDbClient)
    asynchronous = _operations(AsyncCyrockDbClient)
    for name in DELIBERATELY_DIFFERENT_SIGNATURES:
        assert name in synchronous,  f"{name} is exempt from the signature check but missing from the sync client"
        assert name in asynchronous, f"{name} is exempt from the signature check but missing from the async client"


def test_theTwoClients_haveAtLeastTheCollectionOperations() -> None:
    """A smoke check on the guard itself: an empty comparison would pass every test above."""
    expected = {"create_collection", "get_collection", "list_collections", "delete_collection",
                "rename_collection"}
    assert expected <= set(_operations(CyrockDbClient))
    assert expected <= set(_operations(AsyncCyrockDbClient))
