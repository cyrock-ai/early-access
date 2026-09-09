"""The client-side guards from issues #352 / #383.

Each of these rejects at the point the caller binds the value, so the message names the parameter or
field. The failure they exist to prevent is a dimensionless vector reaching a ``SIMILAR TO $v``
clause and producing a confusing result far from its cause.
"""

from __future__ import annotations

import pytest

from cyrock_db.types import QueryParameters, Text, Vector, vector_input


@pytest.mark.parametrize("absent", [None, [], ()])
def test_vector_constructedEmptyOrNone_isRejected(absent: object) -> None:
    """``None`` belongs here as much as ``()``.

    The guard names both and the docstring promises both, but the parameter list used to repeat
    ``[]`` and never pass ``None`` - so the ``values is None`` half of the condition was unasserted.
    Same for the two guards below.
    """
    with pytest.raises(ValueError, match="must not be None or empty"):
        Vector(absent)  # type: ignore[arg-type]


def test_vector_constructedFromValues_isFrozenAndCopied() -> None:
    """A later mutation of the caller's list must not reach the wire."""
    source = [1.0, 2.0, 3.0]
    built  = Vector(source)
    source.append(4.0)

    assert built.values == (1.0, 2.0, 3.0)
    with pytest.raises(AttributeError):
        built.values = (9.0,)  # type: ignore[misc]


def test_vectorInput_fromText_buildsText_andFromValues_buildsVector() -> None:
    assert vector_input("embed me")   == Text("embed me")
    assert vector_input([1.0, 2.0])   == Vector([1.0, 2.0])


@pytest.mark.parametrize("absent", [None, [], ()])
def test_queryParametersVector_emptyOrNone_isRejectedNamingTheParameter(absent: object) -> None:
    with pytest.raises(ValueError, match=r"vector parameter 'v' must not be None or empty"):
        QueryParameters.builder().vector("v", absent)  # type: ignore[arg-type]


@pytest.mark.parametrize("name", [None, "", "   "])
def test_queryParametersVector_blankOrNoneName_isRejectedAtTheBindingSite(name: str) -> None:
    """Rejected here rather than surfacing later as an opaque failure at build time."""
    with pytest.raises(ValueError, match="name must not be None or blank"):
        QueryParameters.builder().vector(name, [1.0])


@pytest.mark.parametrize("name", [None, "", "   "])
def test_queryParametersParam_blankOrNoneName_isRejected(name: str) -> None:
    with pytest.raises(ValueError, match="name must not be None or blank"):
        QueryParameters.builder().param(name, 1)


def test_queryParametersParam_noneValue_isAccepted() -> None:
    """None is a legitimate scalar, unlike an absent vector. The asymmetry is deliberate."""
    assert QueryParameters.builder().param("maybe", None).build().get_scalar("maybe") is None


def test_queryParameters_copiesItsMaps() -> None:
    vectors = {"v": (1.0,)}
    scalars = {"n": 1}
    built   = QueryParameters(vectors=vectors, scalars=scalars)
    vectors["v"] = (9.0,)
    scalars["n"] = 9

    assert built.get_vector("v") == (1.0,)
    assert built.get_scalar("n") == 1


def test_queryParameters_missingParameter_raisesNamingIt() -> None:
    params = QueryParameters.builder().build()
    with pytest.raises(KeyError, match=r"\$absent"):
        params.get_vector("absent")
    with pytest.raises(KeyError, match=r"\$absent"):
        params.get_scalar("absent")
