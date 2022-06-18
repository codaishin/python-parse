"""test parse"""
from dataclasses import dataclass
from datetime import date
from test import UnitTests
from typing import Any, Generic, Iterable, Optional, TypeVar
from unittest.mock import Mock

from parse import (
    KEY_ERROR_MSG,
    TYPE_ERROR_MSG,
    IParser,
    TMatchRating,
    get_parser_default,
)

T = TypeVar("T")


class TestGetParserDefault(UnitTests):
    """test get_parser_default"""


@TestGetParserDefault.describe("parse model")
def _(test: TestGetParserDefault) -> None:
    # pylint: disable=too-few-public-methods
    class _Person:
        name: str
        age: int

    to_person = get_parser_default()(_Person)
    person = to_person({"name": "Harry", "age": 42})
    assert person
    test.assertEqual((person.name, person.age), ("Harry", 42))


@TestGetParserDefault.describe("single value from a single item list")
def _(test: TestGetParserDefault) -> None:
    # pylint: disable=too-few-public-methods
    class _Person:
        name: str
        age: int

    to_person = get_parser_default()(_Person)
    person = to_person({"name": ["Harry"], "age": [42]})
    assert person
    test.assertEqual((person.name, person.age), ("Harry", 42))


@TestGetParserDefault.describe("parse single optional value")
def _(test: TestGetParserDefault) -> None:
    # pylint: disable=too-few-public-methods
    class _Person:
        name: Optional[str]
        age: Optional[int]
        birthday: Optional[date]

    to_person = get_parser_default()(_Person)
    person = to_person({"age": None, "birthday": date(2000, 1, 1)})
    assert person
    test.assertEqual(
        (person.name, person.age, person.birthday),
        (None, None, date(2000, 1, 1)),
    )


@TestGetParserDefault.describe("parse list with optional value")
def _(test: TestGetParserDefault) -> None:
    # pylint: disable=too-few-public-methods
    class _Person:
        names: list[Optional[str]]

    to_person = get_parser_default()(_Person)
    person = to_person({"names": ["Rudy", None]})
    assert person
    test.assertListEqual(person.names, ["Rudy", None])


@TestGetParserDefault.describe("missing key")
def _(test: TestGetParserDefault) -> None:
    # pylint: disable=too-few-public-methods
    class _Person:
        name: str
        age: int

    to_person = get_parser_default()(_Person)
    with test.assertRaises(KeyError) as ctx:
        _ = to_person({"age": 33})

    msg = KEY_ERROR_MSG.format(key="name")
    error = KeyError(msg)
    test.assertEqual(str(error), str(ctx.exception))


@TestGetParserDefault.describe("type mismatch")
def _(test: TestGetParserDefault) -> None:
    # pylint: disable=too-few-public-methods
    class _Car:
        max_speed: int
        seats: int

    to_car = get_parser_default()(_Car)
    with test.assertRaises(TypeError) as ctx:
        _ = to_car({"max_speed": "foo", "seats": "bar"})

    msg = TYPE_ERROR_MSG.format(key="max_speed", type=int)
    error = TypeError(msg)
    test.assertEqual(str(error), str(ctx.exception))


@TestGetParserDefault.describe("type mismatch for generic annotation")
def _(test: TestGetParserDefault) -> None:
    # pylint: disable=too-few-public-methods
    class _Generic(Generic[T]):
        pass

    # pylint: disable=too-few-public-methods
    class _Mock:
        field: _Generic[int]

    to_mock = get_parser_default()(_Mock)
    with test.assertRaises(TypeError) as ctx:
        _ = to_mock({"field": 32})

    msg = TYPE_ERROR_MSG.format(key="field", type=_Generic[int])
    error = TypeError(msg)
    test.assertEqual(str(error), str(ctx.exception))


@TestGetParserDefault.describe("parse nested")
def _(test: TestGetParserDefault) -> None:
    # pylint: disable=too-few-public-methods
    class _Address:
        street: str
        number: int

    # pylint: disable=too-few-public-methods
    class _Person:
        address: _Address
        name: str
        age: int

    to_person = get_parser_default()(_Person)
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
    assert person
    test.assertEqual(
        (
            person.name,
            person.age,
            person.address.street,
            person.address.number,
        ),
        ("Jenny", 22, "Sesame Street", 42),
    )


@TestGetParserDefault.describe("optional nested")
def _(test: TestGetParserDefault) -> None:
    # pylint: disable=too-few-public-methods
    class _Address:
        street: str

    # pylint: disable=too-few-public-methods
    class _Person:
        fst_address: Optional[_Address]
        snd_address: Optional[_Address]
        trd_address: Optional[_Address]

    to_person = get_parser_default()(_Person)
    person = to_person(
        {
            "fst_address": {"street": "Sesame Street"},
            "snd_address": None,
        }
    )

    assert person
    assert person.fst_address
    test.assertEqual(
        (
            person.fst_address.street,
            person.snd_address,
            person.trd_address,
        ),
        ("Sesame Street", None, None),
    )


@TestGetParserDefault.describe("parse dataclass")
def _(test: TestGetParserDefault) -> None:
    @dataclass
    class _Person:
        name: str
        age: int

    to_person = get_parser_default()(_Person)
    person = to_person({"name": "Harry", "age": 42})
    assert person
    test.assertEqual((person.name, person.age), ("Harry", 42))


@TestGetParserDefault.describe("only parse annotations")
def _(test: TestGetParserDefault) -> None:
    # pylint: disable=too-few-public-methods
    class _Person:
        name: str
        age: int
        species = "Human"

    to_person = get_parser_default()(_Person)
    person = to_person({"name": "Harry", "age": 42, "species": "Martian"})
    assert person
    test.assertEqual(
        (person.name, person.age, person.species),
        ("Harry", 42, "Human"),
    )


@TestGetParserDefault.describe("can parse list field")
def _(test: TestGetParserDefault) -> None:
    # pylint: disable=too-few-public-methods
    class _Path:
        nodes: list[str]

    to_path = get_parser_default()(_Path)
    path = to_path({"nodes": ["path", "to", "target"]})
    assert path
    test.assertIsInstance(path.nodes, list)
    test.assertListEqual(
        path.nodes,
        ["path", "to", "target"],
    )


@TestGetParserDefault.describe("can parse tuple field")
def _(test: TestGetParserDefault) -> None:
    # pylint: disable=too-few-public-methods
    class _Path:
        nodes: tuple[str]

    to_path = get_parser_default()(_Path)
    path = to_path({"nodes": ["path", "to", "target"]})
    assert path
    test.assertIsInstance(path.nodes, tuple)
    test.assertListEqual(
        list(path.nodes),
        ["path", "to", "target"],
    )


@TestGetParserDefault.describe("can parse Iterable field")
def _(test: TestGetParserDefault) -> None:
    # pylint: disable=too-few-public-methods
    class _Path:
        nodes: Iterable[str]

    to_path = get_parser_default()(_Path)
    path = to_path({"nodes": ["path", "to", "target"]})
    assert path
    test.assertIsInstance(path.nodes, tuple)
    test.assertListEqual(
        list(path.nodes),
        ["path", "to", "target"],
    )


@TestGetParserDefault.describe("can add Age parser")
def _(test: TestGetParserDefault) -> None:
    class _Age(int):
        ...

    @dataclass
    class _Person:
        age: _Age

    class _AgeParser(IParser[_Age]):
        def match(
            self,
            source_type: type,
            target_type: type[_Age],
        ) -> TMatchRating:
            return 1

        def parse(self, value: Any) -> _Age:
            return _Age(value)

    to_person = get_parser_default(_AgeParser())(_Person)
    person = to_person({"age": 5})
    test.assertEqual(_Person(age=_Age(5)), person)


@TestGetParserDefault.describe("can add Age parser for nested parsing")
def _(test: TestGetParserDefault) -> None:
    class _Age(int):
        ...

    @dataclass
    class _Person:
        age: _Age

    @dataclass
    class _PersonList:
        persons: list[_Person]

    class _AgeParser(IParser[_Age]):
        def match(
            self,
            source_type: type,
            target_type: type[_Age],
        ) -> TMatchRating:
            return 1

        def parse(self, value: Any) -> _Age:
            return _Age(value)

    to_person = get_parser_default(_AgeParser())(_PersonList)
    person_list = to_person({"persons": [{"age": 5}]})
    test.assertEqual(
        _PersonList(persons=[_Person(age=_Age(5))]),
        person_list,
    )


@TestGetParserDefault.describe("use best match")
def _(test: TestGetParserDefault) -> None:
    class _Age(int):
        ...

    @dataclass
    class _Person:
        age: _Age

    class _AgeParser(IParser[_Age]):
        def __init__(self, match: int) -> None:
            self._match = match

        def match(
            self,
            source_type: type,
            target_type: type[_Age],
        ) -> TMatchRating:
            return self._match

        def parse(self, value: Any) -> _Age:
            return _Age(value * self._match)

    to_person = get_parser_default(_AgeParser(1), _AgeParser(2))(_Person)
    person = to_person({"age": 5})
    test.assertEqual(_Person(age=_Age(10)), person)


@TestGetParserDefault.describe(
    "pass source and target type to sub parser's match()"
)
def _(_: TestGetParserDefault) -> None:
    class _Age(int):
        ...

    @dataclass
    class _Person:
        age: _Age

    sub_parser = Mock(
        source_type=int,
        target_type=_Age,
        match=Mock(return_value=1),
        parse=_Age,
    )

    to_person = get_parser_default(sub_parser)(_Person)
    __ = to_person({"age": 5})

    sub_parser.match.assert_called_once_with(int, _Age)


@TestGetParserDefault.describe(
    "pass source and target type to multiple sub parsers' match()"
)
def _(test: TestGetParserDefault) -> None:
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
            parse=_Age,
        )

    sub_parsers = (get_sub_parser(), get_sub_parser(), get_sub_parser())

    to_person = get_parser_default(*sub_parsers)(_Person)
    __ = to_person({"age": 5})

    for i, parser in enumerate(sub_parsers):
        with test.subTest(f"test parsers {i}"):
            parser.match.assert_called_once_with(int, _Age)


@TestGetParserDefault.describe("evaluate parse result type")
def _(test: TestGetParserDefault) -> None:
    @dataclass
    class _Person:
        age: float

    class _StrToFloat(IParser[float]):
        def match(
            self,
            source_type: type,
            target_type: type[float],
        ) -> TMatchRating:
            return 1

        def parse(self, value: Any) -> float:
            return value  # type: ignore

    to_person = get_parser_default(_StrToFloat())(_Person)
    with test.assertRaises(TypeError):
        _ = to_person({"age": "5.1"})


@TestGetParserDefault.describe("parse str")
def _(test: TestGetParserDefault) -> None:
    to_string = get_parser_default()(str)
    test.assertEqual(to_string("hello"), "hello")


@TestGetParserDefault.describe("parse tuple[str]")
def _(test: TestGetParserDefault) -> None:
    to_tuple = get_parser_default()(tuple[str, ...])
    test.assertEqual(to_tuple(("hello", "world")), ("hello", "world"))


@TestGetParserDefault.describe("parse tuple[_Age]")
def _(test: TestGetParserDefault) -> None:
    class _Age(int):
        ...

    class _AgeParser(IParser[_Age]):
        def match(self, source_type: type, target_type: type) -> TMatchRating:
            return 2

        def parse(self, value: Any) -> _Age:
            return _Age(value)

    to_tuple = get_parser_default(_AgeParser())(tuple[_Age, ...])
    test.assertEqual(to_tuple((4, 6)), (_Age(4), _Age(6)))


@TestGetParserDefault.describe("parse tuple item type mismatch")
def _(test: TestGetParserDefault) -> None:
    to_tuple = get_parser_default()(tuple[str])
    with test.assertRaises(TypeError):
        _ = to_tuple((1, 2, 3))
