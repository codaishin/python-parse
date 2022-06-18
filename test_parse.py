"""test parse"""
from dataclasses import dataclass
from datetime import date
from test import UnitTests
from typing import Generic, Iterable, Optional, TypeVar
from unittest.mock import Mock

from parse import (
    KEY_ERROR_MSG,
    TYPE_ERROR_MSG,
    TMatchRating,
    ValueParser,
    get_parser,
)

T = TypeVar("T")


class TestGetParser(UnitTests):
    """test get_parser"""


@TestGetParser.describe("parse model")
def _(test: TestGetParser) -> None:
    # pylint: disable=too-few-public-methods
    class _Person:
        name: str
        age: int

    to_person = get_parser()(_Person)
    person = to_person({"name": "Harry", "age": 42})
    test.assertEqual((person.name, person.age), ("Harry", 42))


@TestGetParser.describe("single value from a single item list")
def _(test: TestGetParser) -> None:
    # pylint: disable=too-few-public-methods
    class _Person:
        name: str
        age: int

    to_person = get_parser()(_Person)
    person = to_person({"name": ["Harry"], "age": [42]})
    test.assertEqual((person.name, person.age), ("Harry", 42))


@TestGetParser.describe("parse single optional value")
def _(test: TestGetParser) -> None:
    # pylint: disable=too-few-public-methods
    class _Person:
        name: Optional[str]
        age: Optional[int]
        birthday: Optional[date]

    to_person = get_parser()(_Person)
    person = to_person({"age": None, "birthday": date(2000, 1, 1)})
    test.assertEqual(
        (person.name, person.age, person.birthday),
        (None, None, date(2000, 1, 1)),
    )


@TestGetParser.describe("parse list with optional value")
def _(test: TestGetParser) -> None:
    # pylint: disable=too-few-public-methods
    class _Person:
        names: list[Optional[str]]

    to_person = get_parser()(_Person)
    person = to_person({"names": ["Rudy", None]})
    test.assertListEqual(person.names, ["Rudy", None])


@TestGetParser.describe("missing key")
def _(test: TestGetParser) -> None:
    # pylint: disable=too-few-public-methods
    class _Person:
        name: str
        age: int

    to_person = get_parser()(_Person)
    with test.assertRaises(KeyError) as ctx:
        _ = to_person({"age": 33})

    msg = KEY_ERROR_MSG.format(key="name")
    error = KeyError(msg)
    test.assertEqual(str(error), str(ctx.exception))


@TestGetParser.describe("type mismatch")
def _(test: TestGetParser) -> None:
    # pylint: disable=too-few-public-methods
    class _Car:
        max_speed: int
        seats: int

    to_car = get_parser()(_Car)
    with test.assertRaises(TypeError) as ctx:
        _ = to_car({"max_speed": "foo", "seats": "bar"})

    msg = TYPE_ERROR_MSG.format(key="max_speed", type=int)
    error = TypeError(msg)
    test.assertEqual(str(error), str(ctx.exception))


@TestGetParser.describe("type mismatch for generic annotation")
def _(test: TestGetParser) -> None:
    # pylint: disable=too-few-public-methods
    class _Generic(Generic[T]):
        pass

    # pylint: disable=too-few-public-methods
    class _Mock:
        field: _Generic[int]

    to_mock = get_parser()(_Mock)
    with test.assertRaises(TypeError) as ctx:
        _ = to_mock({"field": 32})

    msg = TYPE_ERROR_MSG.format(key="field", type=_Generic[int])
    error = TypeError(msg)
    test.assertEqual(str(error), str(ctx.exception))


@TestGetParser.describe("parse nested")
def _(test: TestGetParser) -> None:
    # pylint: disable=too-few-public-methods
    class _Address:
        street: str
        number: int

    # pylint: disable=too-few-public-methods
    class _Person:
        address: _Address
        name: str
        age: int

    to_person = get_parser()(_Person)
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


@TestGetParser.describe("optional nested")
def _(test: TestGetParser) -> None:
    # pylint: disable=too-few-public-methods
    class _Address:
        street: str

    # pylint: disable=too-few-public-methods
    class _Person:
        fst_address: Optional[_Address]
        snd_address: Optional[_Address]
        trd_address: Optional[_Address]

    to_person = get_parser()(_Person)
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


@TestGetParser.describe("parse dataclass")
def _(test: TestGetParser) -> None:
    @dataclass
    class _Person:
        name: str
        age: int

    to_person = get_parser()(_Person)
    person = to_person({"name": "Harry", "age": 42})
    test.assertEqual((person.name, person.age), ("Harry", 42))


@TestGetParser.describe("only parse annotations")
def _(test: TestGetParser) -> None:
    # pylint: disable=too-few-public-methods
    class _Person:
        name: str
        age: int
        species = "Human"

    to_person = get_parser()(_Person)
    person = to_person({"name": "Harry", "age": 42, "species": "Martian"})
    test.assertEqual(
        (person.name, person.age, person.species),
        ("Harry", 42, "Human"),
    )


@TestGetParser.describe("can parse list field")
def _(test: TestGetParser) -> None:
    # pylint: disable=too-few-public-methods
    class _Path:
        nodes: list[str]

    to_path = get_parser()(_Path)
    path = to_path({"nodes": ["path", "to", "target"]})
    test.assertIsInstance(path.nodes, list)
    test.assertListEqual(
        path.nodes,
        ["path", "to", "target"],
    )


@TestGetParser.describe("can parse tuple field")
def _(test: TestGetParser) -> None:
    # pylint: disable=too-few-public-methods
    class _Path:
        nodes: tuple[str]

    to_path = get_parser()(_Path)
    path = to_path({"nodes": ["path", "to", "target"]})
    test.assertIsInstance(path.nodes, tuple)
    test.assertListEqual(
        list(path.nodes),
        ["path", "to", "target"],
    )


@TestGetParser.describe("can parse Iterable field")
def _(test: TestGetParser) -> None:
    # pylint: disable=too-few-public-methods
    class _Path:
        nodes: Iterable[str]

    to_path = get_parser()(_Path)
    path = to_path({"nodes": ["path", "to", "target"]})
    test.assertIsInstance(path.nodes, tuple)
    test.assertListEqual(
        list(path.nodes),
        ["path", "to", "target"],
    )


@TestGetParser.describe("can add Age parser")
def _(test: TestGetParser) -> None:
    class _Age(int):
        ...

    @dataclass
    class _Person:
        age: _Age

    class _AgeParser(ValueParser[int, _Age]):
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

    to_person = get_parser(_AgeParser())(_Person)
    person = to_person({"age": 5})
    test.assertEqual(_Person(age=_Age(5)), person)


@TestGetParser.describe("can add Age parser for nested parsing")
def _(test: TestGetParser) -> None:
    class _Age(int):
        ...

    @dataclass
    class _Person:
        age: _Age

    @dataclass
    class _PersonList:
        persons: list[_Person]

    class _AgeParser(ValueParser[int, _Age]):
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

    to_person = get_parser(_AgeParser())(_PersonList)
    person_list = to_person({"persons": [{"age": 5}]})
    test.assertEqual(
        _PersonList(persons=[_Person(age=_Age(5))]),
        person_list,
    )


@TestGetParser.describe("use best match")
def _(test: TestGetParser) -> None:
    class _Age(int):
        ...

    @dataclass
    class _Person:
        age: _Age

    class _AgeParser(ValueParser[int, _Age]):
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

    to_person = get_parser(_AgeParser(1), _AgeParser(2))(_Person)
    person = to_person({"age": 5})
    test.assertEqual(_Person(age=_Age(10)), person)


@TestGetParser.describe("pass source and target type to sub parser's match()")
def _(_: TestGetParser) -> None:
    class _Age(int):
        ...

    @dataclass
    class _Person:
        age: _Age

    sub_parser = Mock(
        source_type=int,
        target_type=_Age,
        match=Mock(return_value=1),
    )

    to_person = get_parser(sub_parser)(_Person)
    __ = to_person({"age": 5})

    sub_parser.match.assert_called_once_with(int, _Age)


@TestGetParser.describe(
    "pass source and target type to multiple sub parsers' match()"
)
def _(test: TestGetParser) -> None:
    class _Age(int):
        ...

    @dataclass
    class _Person:
        age: _Age

    def get_sub_parser() -> Mock:
        return Mock(
            source_type=int,
            target_type=_Age,
            match=Mock(return_value=1),
        )

    sub_parsers = (get_sub_parser(), get_sub_parser(), get_sub_parser())

    to_person = get_parser(*sub_parsers)(_Person)
    __ = to_person({"age": 5})

    for i, parser in enumerate(sub_parsers):
        with test.subTest(f"test parsers {i}"):
            parser.match.assert_called_once_with(int, _Age)


@TestGetParser.describe("evaluate TSource outside of sub parser's match")
def _(test: TestGetParser) -> None:
    @dataclass
    class _Person:
        age: float

    class _StrToFloat(ValueParser[str, float]):
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

    to_person = get_parser(_StrToFloat())(_Person)
    with test.assertRaises(TypeError):
        _ = to_person({"age": 5})


@TestGetParser.describe("evaluate TTarget outside of sub parser's match")
def _(test: TestGetParser) -> None:
    @dataclass
    class _Person:
        age: int

    class _StrToFloat(ValueParser[str, float]):
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

    to_person = get_parser(_StrToFloat())(_Person)
    with test.assertRaises(TypeError):
        _ = to_person({"age": "5.1"})
