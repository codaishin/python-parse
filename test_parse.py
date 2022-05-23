"""test parse"""
from dataclasses import dataclass
from datetime import date
from typing import Generic, Iterable, Optional, TypeVar
from test import UnitTests
from parse import Parse

T = TypeVar("T")


class TestParse(UnitTests):
    """test Parse"""


@TestParse.describe("parse model")
def _(test: TestParse) -> None:
    # pylint: disable=too-few-public-methods
    class _Person:
        name: str
        age: int

    to_person = Parse(_Person)
    person = to_person({"name": "Harry", "age": 42})
    test.assertEqual((person.name, person.age), ("Harry", 42))


@TestParse.describe("single value from a single item list")
def _(test: TestParse) -> None:
    # pylint: disable=too-few-public-methods
    class _Person:
        name: str
        age: int

    to_person = Parse(_Person)
    person = to_person({"name": ["Harry"], "age": [42]})
    test.assertEqual((person.name, person.age), ("Harry", 42))


@TestParse.describe("parse single optional value")
def _(test: TestParse) -> None:
    # pylint: disable=too-few-public-methods
    class _Person:
        name: Optional[str]
        age: Optional[int]
        birthday: Optional[date]

    to_person = Parse(_Person)
    person = to_person({"age": None, "birthday": date(2000, 1, 1)})
    test.assertEqual(
        (person.name, person.age, person.birthday),
        (None, None, date(2000, 1, 1)),
    )


@TestParse.describe("parse list with optional value")
def _(test: TestParse) -> None:
    # pylint: disable=too-few-public-methods
    class _Person:
        names: list[Optional[str]]

    to_person = Parse(_Person)
    person = to_person({"names": ["Rudy", None]})
    test.assertListEqual(person.names, ["Rudy", None])


@TestParse.describe("missing key")
def _(test: TestParse) -> None:
    # pylint: disable=too-few-public-methods
    class _Person:
        name: str
        age: int

    to_person = Parse(_Person)
    with test.assertRaises(KeyError) as ctx:
        _ = to_person({"age": 33})

    msg = Parse.KEY_ERROR.format(key="name")
    error = KeyError(msg)
    test.assertEqual(str(error), str(ctx.exception))


@TestParse.describe("type mismatch")
def _(test: TestParse) -> None:
    # pylint: disable=too-few-public-methods
    class _Car:
        max_speed: int
        seats: int

    to_car = Parse(_Car)
    with test.assertRaises(TypeError) as ctx:
        _ = to_car({"max_speed": "foo", "seats": "bar"})

    msg = Parse.TYPE_ERROR.format(key="max_speed", type=int)
    error = TypeError(msg)
    test.assertEqual(str(error), str(ctx.exception))


@TestParse.describe("type mismatch for generic annotation")
def _(test: TestParse) -> None:
    # pylint: disable=too-few-public-methods
    class _Generic(Generic[T]):
        pass

    # pylint: disable=too-few-public-methods
    class _Mock:
        field: _Generic[int]

    to_mock = Parse(_Mock)
    with test.assertRaises(TypeError) as ctx:
        _ = to_mock({"field": 32})

    msg = Parse.TYPE_ERROR.format(key="field", type=_Generic[int])
    error = TypeError(msg)
    test.assertEqual(str(error), str(ctx.exception))


@TestParse.describe("parse nested")
def _(test: TestParse) -> None:
    # pylint: disable=too-few-public-methods
    class _Address:
        street: str
        number: int

    # pylint: disable=too-few-public-methods
    class _Person:
        address: _Address
        name: str
        age: int

    to_person = Parse(_Person)
    person = to_person(
        {
            "name": "Jenny",
            "age": 22,
            "address": {
                "street": "Sesame Street",
                "number": 42,
            },
        }
    )
    test.assertEqual(
        (
            person.name,
            person.age,
            person.address.street,
            person.address.number,
        ),
        ("Jenny", 22, "Sesame Street", 42),
    )


@TestParse.describe("optional nested")
def _(test: TestParse) -> None:
    # pylint: disable=too-few-public-methods
    class _Address:
        street: str

    # pylint: disable=too-few-public-methods
    class _Person:
        fst_address: Optional[_Address]
        snd_address: Optional[_Address]
        trd_address: Optional[_Address]

    to_person = Parse(_Person)
    person = to_person(
        {
            "fst_address": {"street": "Sesame Street"},
            "snd_address": None,
        }
    )

    assert person.fst_address
    test.assertEqual(
        (
            person.fst_address.street,
            person.snd_address,
            person.trd_address,
        ),
        ("Sesame Street", None, None),
    )


@TestParse.describe("parse dataclass")
def _(test: TestParse) -> None:
    @dataclass
    class _Person:
        name: str
        age: int

    to_person = Parse(_Person)
    person = to_person({"name": "Harry", "age": 42})
    test.assertEqual((person.name, person.age), ("Harry", 42))


@TestParse.describe("only parse annotations")
def _(test: TestParse) -> None:
    # pylint: disable=too-few-public-methods
    class _Person:
        name: str
        age: int
        species = "Human"

    to_person = Parse(_Person)
    person = to_person({"name": "Harry", "age": 42, "species": "Martian"})
    test.assertEqual(
        (person.name, person.age, person.species),
        ("Harry", 42, "Human"),
    )


@TestParse.describe("can parse list field")
def _(test: TestParse) -> None:
    # pylint: disable=too-few-public-methods
    class _Path:
        nodes: list[str]

    to_path = Parse(_Path)
    path = to_path({"nodes": ["path", "to", "target"]})
    test.assertIsInstance(path.nodes, list)
    test.assertListEqual(
        path.nodes,
        ["path", "to", "target"],
    )


@TestParse.describe("can parse tuple field")
def _(test: TestParse) -> None:
    # pylint: disable=too-few-public-methods
    class _Path:
        nodes: tuple[str]

    to_path = Parse(_Path)
    path = to_path({"nodes": ["path", "to", "target"]})
    test.assertIsInstance(path.nodes, tuple)
    test.assertListEqual(
        list(path.nodes),
        ["path", "to", "target"],
    )


@TestParse.describe("can parse Iterable field")
def _(test: TestParse) -> None:
    # pylint: disable=too-few-public-methods
    class _Path:
        nodes: Iterable[str]

    to_path = Parse(_Path)
    path = to_path({"nodes": ["path", "to", "target"]})
    test.assertIsInstance(path.nodes, tuple)
    test.assertListEqual(
        list(path.nodes),
        ["path", "to", "target"],
    )
