from collections import defaultdict
from typing import ClassVar, cast

import pytest

from accumulate import Order, accumulate


def test_accumulate():
    class A:
        x: ClassVar = [1]  # You can start with a plain container
        y = accumulate({"a": 1})  # Or an accumulating one

    assert A.x == A().x == [1]
    assert A.y == A().y == {"a": 1}

    class B(A):
        x = accumulate([2])  # And build up along the way
        y = accumulate({"b": 2})

    assert B.x == B().x == [1, 2]
    assert B.y == B().y == {"a": 1, "b": 2}

    class C(B):
        x: ClassVar = [3]  # Or, override the accumulation with a single value

    assert C.x == C().x == [3]
    assert C.y == C().y == {"a": 1, "b": 2}

    class D(C):
        x = accumulate([4])  # If you accumulate again, it'll be limited

    assert D.x == D().x == [3, 4]
    assert D.y == D().y == {"a": 1, "b": 2}


@pytest.mark.parametrize(
    ("values", "order", "expected"),
    [
        (([1], [2]), "parent-first", [1, 2]),
        (([1], [2]), "parent-last", [2, 1]),
        (
            ({"a": 1}, {"a": 2, "b": 2}),
            "parent-first",
            {"a": 2, "b": 2},
        ),
        (
            # NOTE: "parent-last" with duplicate keys with will prefer the parent value.
            ({"a": 1}, {"a": 2, "b": 2}),
            "parent-last",
            {"a": 1, "b": 2},
        ),
    ],
)
def test_accumulate_order[T](values: tuple[T, T], order: Order, expected: T):
    a, b = values

    class A:
        x = accumulate(a)

    class B(A):
        x = accumulate(b, order=order)

    assert B.x == expected


def test_accumulate_override():
    class A:
        x = accumulate([1])

    class B(A):
        x = accumulate([2])

    # You can also override on an instance without affecting the class values.
    override = B()
    override.x = [-1]
    assert B.x == [1, 2]
    assert override.x == [-1]


@pytest.mark.parametrize(
    ("msg", "chain_values", "expected"),
    [
        (
            "it should handle lists",
            [[1], [2], [3]],
            [1, 2, 3],
        ),
        (
            "it should handle tuples",
            [(1,), (2,), (3,)],
            (1, 2, 3),
        ),
        (
            "it should handle sets",
            [{1}, {2}, {2}],
            {1, 2},
        ),
        (
            "it should handle dicts",
            [{"a": 1}, {"b": 2}, {"b": -2}],
            {"a": 1, "b": -2},
        ),
        (
            "it should handle defaultdicts",
            [
                defaultdict(int, a=1),
                defaultdict(int, b=2),
                defaultdict(int, b=-2),
            ],
            {"a": 1, "b": -2},
        ),
    ],
)
def test_accumulate_types[T](msg: str, chain_values: list[T], expected: T) -> None:
    output = gen_classes(*chain_values)
    assert output == expected, msg


def gen_classes[T](value: T, *values: T) -> T:
    """Generate the chain of classes with `attr` set to the successive values in `values` and return the last one."""

    class Foo:
        x = accumulate(value)

    for value in values:

        class Sub(Foo):
            x = accumulate(value)

        Foo = cast(type[Foo], Sub)
    return Foo.x
