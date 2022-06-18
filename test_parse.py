"""test parse"""
from dataclasses import dataclass
from datetime import date
from test import UnitTests
from typing import Generic, Iterable, Optional, TypeVar
from unittest.mock import Mock

from parse import Parse, SubParser, TMatchRating

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


@TestParse.describe("can add Age parser")
def _(test: TestParse) -> None:
    class _Age(int):
        ...

    @dataclass
    class _Person:
        age: _Age

    class _AgeParser(SubParser[int, _Age]):
        def __init__(self) -> None:
            super().__init__(int, _Age)

        def match(
            self,
            source_type: type[int],
            target_type: type[_Age],
        ) -> TMatchRating:
            return 1

        def parse(self, value: int) -> _Age:
            return _Age(value)

    to_person = Parse(_Person, (_AgeParser(),))
    person = to_person({"age": 5})
    test.assertEqual(_Person(age=_Age(5)), person)


@TestParse.describe("can add Age parser for nested parsing")
def _(test: TestParse) -> None:
    class _Age(int):
        ...

    @dataclass
    class _Person:
        age: _Age

    @dataclass
    class _PersonList:
        persons: list[_Person]

    class _AgeParser(SubParser[int, _Age]):
        def __init__(self) -> None:
            super().__init__(int, _Age)

        def match(
            self,
            source_type: type[int],
            target_type: type[_Age],
        ) -> TMatchRating:
            return 1

        def parse(self, value: int) -> _Age:
            return _Age(value)

    to_person = Parse(_PersonList, (_AgeParser(),))
    person_list = to_person({"persons": [{"age": 5}]})
    test.assertEqual(
        _PersonList(persons=[_Person(age=_Age(5))]),
        person_list,
    )


@TestParse.describe("use best match")
def _(test: TestParse) -> None:
    class _Age(int):
        ...

    @dataclass
    class _Person:
        age: _Age

    class _AgeParser(SubParser[int, _Age]):
        def __init__(self, match: int) -> None:
            super().__init__(int, _Age)
            self._match = match

        def match(
            self,
            source_type: type[int],
            target_type: type[_Age],
        ) -> TMatchRating:
            return self._match

        def parse(self, value: int) -> _Age:
            return _Age(value * self._match)

    to_person = Parse(_Person, (_AgeParser(1), _AgeParser(2)))
    person = to_person({"age": 5})
    test.assertEqual(_Person(age=_Age(10)), person)


@TestParse.describe("pass source and target type to sub parser's match()")
def _(_: TestParse) -> None:
    class _Age(int):
        ...

    @dataclass
    class _Person:
        age: _Age

    parser = Mock(
        source_type=int,
        target_type=_Age,
        match=Mock(return_value=1),
    )

    to_person = Parse(_Person, (parser,))
    __ = to_person({"age": 5})

    parser.match.assert_called_once_with(int, _Age)


@TestParse.describe(
    "pass source and target type to multiple sub parsers' match()"
)
def _(test: TestParse) -> None:
    class _Age(int):
        ...

    @dataclass
    class _Person:
        age: _Age

    def get_parser() -> Mock:
        return Mock(
            source_type=int,
            target_type=_Age,
            match=Mock(return_value=1),
        )

    parsers = (get_parser(), get_parser(), get_parser())

    to_person = Parse(_Person, parsers)
    __ = to_person({"age": 5})

    for i, parser in enumerate(parsers):
        with test.subTest(f"test parsers {i}"):
            parser.match.assert_called_once_with(int, _Age)


@TestParse.describe("evaluate TSource outside of sub parser's match")
def _(test: TestParse) -> None:
    @dataclass
    class _Person:
        age: float

    class _StrToFloat(SubParser[str, float]):
        def __init__(self) -> None:
            super().__init__(str, float)

        def match(
            self,
            source_type: type[str],
            target_type: type[float],
        ) -> TMatchRating:
            return 1

        def parse(self, value: str) -> float:
            return float(value)

    to_person = Parse(_Person, (_StrToFloat(),))
    with test.assertRaises(TypeError):
        _ = to_person({"age": 5})


@TestParse.describe("evaluate TTarget outside of sub parser's match")
def _(test: TestParse) -> None:
    @dataclass
    class _Person:
        age: int

    class _StrToFloat(SubParser[str, float]):
        def __init__(self) -> None:
            super().__init__(str, float)

        def match(
            self,
            source_type: type[str],
            target_type: type[float],
        ) -> TMatchRating:
            return 1

        def parse(self, value: str) -> float:
            return float(value)

    to_person = Parse(_Person, (_StrToFloat(),))
    with test.assertRaises(TypeError):
        _ = to_person({"age": "5.1"})
