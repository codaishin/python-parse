"""test parse"""
from dataclasses import dataclass
from datetime import date
from typing import Any, Generic, Iterable, Optional
from unittest.mock import Mock, call

from python_parse.parse import KEY_ERROR_MSG, TYPE_ERROR_MSG, get_parser
from python_parse.types import NoMatch, T

from tests.test import UnitTests


class TestGetParserDefault(UnitTests):
    """test get_parser_default"""


@TestGetParserDefault.describe("parse model")
def _(test: TestGetParserDefault) -> None:
    # pylint: disable=too-few-public-methods
    class _Person:
        name: str
        age: int

    to_person = get_parser()(_Person)
    person = to_person({"name": "Harry", "age": 42})
    assert person
    test.assertEqual((person.name, person.age), ("Harry", 42))


@TestGetParserDefault.describe("parse single optional value")
def _(test: TestGetParserDefault) -> None:
    # pylint: disable=too-few-public-methods
    class _Person:
        name: Optional[str]
        age: Optional[int]
        birthday: Optional[date]

    to_person = get_parser()(_Person)
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

    to_person = get_parser()(_Person)
    person = to_person({"names": ["Rudy", None]})
    assert person
    test.assertListEqual(person.names, ["Rudy", None])


@TestGetParserDefault.describe("missing key")
def _(test: TestGetParserDefault) -> None:
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


@TestGetParserDefault.describe("type mismatch")
def _(test: TestGetParserDefault) -> None:
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


@TestGetParserDefault.describe("type mismatch for generic annotation")
def _(test: TestGetParserDefault) -> None:
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

    to_person = get_parser()(_Person)
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

    to_person = get_parser()(_Person)
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

    to_person = get_parser()(_Person)
    person = to_person({"name": "Harry", "age": 42, "species": "Martian"})
    assert person
    test.assertEqual(
        (person.name, person.age, person.species),
        ("Harry", 42, "Human"),
    )


@TestGetParserDefault.describe("can parse list[str] field")
def _(test: TestGetParserDefault) -> None:
    # pylint: disable=too-few-public-methods
    class _Path:
        nodes: list[str]

    to_path = get_parser()(_Path)
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
        nodes: tuple[str, ...]

    to_path = get_parser()(_Path)
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

    to_path = get_parser()(_Path)
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

    def parse_age(source_value: Any, _: type[_Age]) -> _Age | NoMatch:
        return _Age(source_value)

    to_person = get_parser(parse_age)(_Person)
    person = to_person({"age": 5})
    test.assertEqual(_Person(age=_Age(5)), person)


@TestGetParserDefault.describe("can add Age parser for list parsing")
def _(test: TestGetParserDefault) -> None:
    class _Age(int):
        ...

    @dataclass
    class _Person:
        age: _Age

    @dataclass
    class _PersonList:
        persons: list[_Person]

    def parse_age(source_value: Any, target_type: type) -> _Age | NoMatch:
        if not isinstance(source_value, int):
            return NoMatch()
        if not issubclass(target_type, _Age):
            return NoMatch()
        return _Age(source_value)

    to_person = get_parser(parse_age)(_PersonList)
    person_list = to_person({"persons": [{"age": 5}]})
    test.assertEqual(
        _PersonList(persons=[_Person(age=_Age(5))]),
        person_list,
    )


@TestGetParserDefault.describe("use first match")
def _(test: TestGetParserDefault) -> None:
    class _ShouldNotBeUsed(Exception):
        ...

    class _Age(int):
        ...

    @dataclass
    class _Person:
        age: _Age

    def parse_age(source_value: Any, _: type[_Age]) -> _Age | NoMatch:
        return _Age(source_value)

    def parse_age_raise(source_value: Any, _: type[_Age]) -> _Age | NoMatch:
        raise _ShouldNotBeUsed()

    to_person = get_parser(parse_age, parse_age_raise)(_Person)

    try:
        _ = to_person({"age": 5})
    except _ShouldNotBeUsed:
        test.fail("invoked parser that should not have been invoked")


@TestGetParserDefault.describe(
    "pass source and target type to sub parser's match()"
)
def _(_: TestGetParserDefault) -> None:
    class _Age(int):
        ...

    @dataclass
    class _Person:
        age: _Age

    parse_age = Mock(return_value=_Age(5))

    to_person = get_parser(parse_age)(_Person)
    __ = to_person({"age": 5})

    parse_age.assert_called_once_with(5, _Age)


@TestGetParserDefault.describe(
    "pass source value and target type to multiple parsers when previous"
    "parser did not suffice"
)
def _(_: TestGetParserDefault) -> None:
    class _Age(int):
        ...

    class _Mail(str):
        ...

    class _Gender(str):
        ...

    @dataclass
    class _Person:
        age: _Age
        mail: _Mail
        gender: _Gender

    def from_to(src_type: type, ctr: type) -> Mock:
        def parse(source_value: Any, target_type: type) -> Any | NoMatch:
            if not isinstance(source_value, src_type):
                return NoMatch()
            if not issubclass(ctr, target_type):
                return NoMatch()
            return ctr(source_value)  # type: ignore

        return Mock(side_effect=parse)

    age = from_to(int, _Age)
    mail = from_to(str, _Mail)
    gender = from_to(str, _Gender)

    to_person = get_parser(age, mail, gender)(_Person)

    __ = to_person(
        {
            "age": 24,
            "mail": "my.mail@example.com",
            "gender": "fluffy",
        }
    )

    calls = (
        call(24, _Age),
        call("my.mail@example.com", _Mail),
        call("fluffy", _Gender),
    )

    age.assert_has_calls(calls)
    mail.assert_has_calls(calls[1:])
    gender.assert_has_calls(calls[2:])


@TestGetParserDefault.describe("evaluate parse result type")
def _(test: TestGetParserDefault) -> None:
    @dataclass
    class _Person:
        age: float

    def str_to_float(source_value: Any, _: type[float]) -> float | NoMatch:
        return source_value  # type: ignore

    to_person = get_parser(str_to_float)(_Person)
    with test.assertRaises(TypeError):
        _ = to_person({"age": "5.1"})


@TestGetParserDefault.describe("parse str")
def _(test: TestGetParserDefault) -> None:
    to_string = get_parser()(str)
    test.assertEqual(to_string("hello"), "hello")


@TestGetParserDefault.describe("parse tuple[str]")
def _(test: TestGetParserDefault) -> None:
    to_tuple = get_parser()(tuple[str, ...])
    test.assertEqual(to_tuple(("hello", "world")), ("hello", "world"))


@TestGetParserDefault.describe("parse tuple[_Age]")
def _(test: TestGetParserDefault) -> None:
    class _Age(int):
        ...

    def parse_age(source_value: Any, target_type: type) -> _Age | NoMatch:
        if not isinstance(source_value, int):
            return NoMatch()
        if not issubclass(target_type, _Age):
            return NoMatch()
        return _Age(source_value)

    to_tuple = get_parser(parse_age)(tuple[_Age, ...])
    result = to_tuple((4, 6))
    test.assertEqual(result, (_Age(4), _Age(6)))


@TestGetParserDefault.describe("parse tuple item type mismatch")
def _(test: TestGetParserDefault) -> None:
    to_tuple = get_parser()(tuple[str, ...])
    with test.assertRaises(TypeError):
        _ = to_tuple((1, 2, 3))
