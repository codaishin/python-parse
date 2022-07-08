"""test parse"""
from dataclasses import dataclass
from datetime import date
from typing import Any, Generic, Optional
from unittest.mock import Mock, call

from python_parse.parse import (
    DEFAULT_MATCHERS,
    KEY_ERROR_MSG,
    TYPE_ERROR_MSG,
    get_parser,
    get_parser_with_no_defaults,
)
from python_parse.types import NoMatch, T

from tests.test import UnitTests


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


@TestGetParser.describe("parse single optional value")
def _(test: TestGetParser) -> None:
    # pylint: disable=too-few-public-methods
    class _Person:
        name: str | None
        age: int | None
        birthday: date | None

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


@TestGetParser.describe("can parse list[str] field")
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
        nodes: tuple[str, ...]

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

    def match_age(source_value: Any, _: type[_Age]) -> _Age | NoMatch:
        return _Age(source_value)

    to_person = get_parser(matchers=(match_age,))(_Person)
    person = to_person({"age": 5})
    test.assertEqual(_Person(age=_Age(5)), person)


@TestGetParser.describe("can add Age parser for list parsing")
def _(test: TestGetParser) -> None:
    class _Age(int):
        ...

    @dataclass
    class _Person:
        age: _Age

    @dataclass
    class _PersonList:
        persons: list[_Person]

    def match_age(source_value: Any, target_type: type) -> _Age | NoMatch:
        if not isinstance(source_value, int):
            return NoMatch()
        if not issubclass(target_type, _Age):
            return NoMatch()
        return _Age(source_value)

    to_person = get_parser(matchers=(match_age,))(_PersonList)
    person_list = to_person({"persons": [{"age": 5}]})
    test.assertEqual(
        _PersonList(persons=[_Person(age=_Age(5))]),
        person_list,
    )


@TestGetParser.describe("use first match")
def _(test: TestGetParser) -> None:
    class _ShouldNotBeUsed(Exception):
        ...

    class _Age(int):
        ...

    @dataclass
    class _Person:
        age: _Age

    def match_age(source_value: Any, _: type[_Age]) -> _Age | NoMatch:
        return _Age(source_value)

    def match_age_raise(_: Any, __: type[_Age]) -> _Age | NoMatch:
        raise _ShouldNotBeUsed()

    parser = get_parser(matchers=(match_age, match_age_raise))
    to_person = parser(_Person)

    try:
        _ = to_person({"age": 5})
    except _ShouldNotBeUsed:
        test.fail("invoked parser that should not have been invoked")


@TestGetParser.describe("pass source and target type to sub parser's match()")
def _(_: TestGetParser) -> None:
    class _Age(int):
        ...

    @dataclass
    class _Person:
        age: _Age

    match_age = Mock(return_value=_Age(5))

    to_person = get_parser(matchers=(match_age,))(_Person)
    __ = to_person({"age": 5})

    match_age.assert_called_once_with(5, _Age)


@TestGetParser.describe(
    "pass source value and target type to multiple parsers when previous"
    "parser did not suffice"
)
def _(_: TestGetParser) -> None:
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

    to_person = get_parser(matchers=(age, mail, gender))(_Person)

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


@TestGetParser.describe("evaluate parse result type")
def _(test: TestGetParser) -> None:
    @dataclass
    class _Person:
        age: float

    def str_to_float(source_value: Any, _: type[float]) -> float | NoMatch:
        return source_value  # type: ignore

    to_person = get_parser(matchers=(str_to_float,))(_Person)
    with test.assertRaises(TypeError):
        _ = to_person({"age": "5.1"})


@TestGetParser.describe("parse str")
def _(test: TestGetParser) -> None:
    to_string = get_parser()(str)
    test.assertEqual(to_string("hello"), "hello")


@TestGetParser.describe("parse tuple[str]")
def _(test: TestGetParser) -> None:
    to_tuple = get_parser()(tuple[str, ...])
    test.assertEqual(to_tuple(("hello", "world")), ("hello", "world"))


@TestGetParser.describe("parse tuple[_Age]")
def _(test: TestGetParser) -> None:
    class _Age(int):
        ...

    def match_age(source_value: Any, target_type: type) -> _Age | NoMatch:
        if not isinstance(source_value, int):
            return NoMatch()
        if not issubclass(target_type, _Age):
            return NoMatch()
        return _Age(source_value)

    to_tuple = get_parser(matchers=(match_age,))(tuple[_Age, ...])
    result = to_tuple((4, 6))
    test.assertEqual(result, (_Age(4), _Age(6)))


@TestGetParser.describe("parse tuple item type mismatch")
def _(test: TestGetParser) -> None:
    to_tuple = get_parser()(tuple[str, ...])
    with test.assertRaises(TypeError):
        _ = to_tuple((1, 2, 3))


@TestGetParser.describe("parse dict to dict")
def _(test: TestGetParser) -> None:
    to_data = get_parser()(dict[str, int])
    data = to_data({"a": 24, "b": 42})
    test.assertEqual(data, {"a": 24, "b": 42})


@TestGetParser.describe("parse dict to dict type error for value")
def _(test: TestGetParser) -> None:
    to_data = get_parser()(dict[str, int])
    with test.assertRaises(TypeError):
        _ = to_data({"a": "24", "b": 42})


@TestGetParser.describe("parse dict to dict type error for key")
def _(test: TestGetParser) -> None:
    to_data = get_parser()(dict[str, int])
    with test.assertRaises(TypeError):
        _ = to_data({"a": 24, 11: 42})


@TestGetParser.describe("parse union")
def _(test: TestGetParser) -> None:
    @dataclass
    class _Person:
        age: str | int | float

    to_person = get_parser()(_Person)

    person = to_person({"age": "44"})
    test.assertEqual(person.age, "44")

    person = to_person({"age": 44})
    test.assertEqual(person.age, 44)

    person = to_person({"age": 44.4})
    test.assertEqual(person.age, 44.4)


@TestGetParser.describe("parse tuple with different types")
def _(test: TestGetParser) -> None:
    @dataclass
    class _Person:
        data: tuple[str, int, bool]

    to_person = get_parser()(_Person)

    person = to_person({"data": ["33", 33, True]})
    test.assertEqual(person.data, ("33", 33, True))


class TestGetParserWithNoDefault(UnitTests):
    """test get_parser_with_no_default"""


@TestGetParserWithNoDefault.describe("also uses default generic validators")
def _(test: TestGetParserWithNoDefault) -> None:
    @dataclass
    class _Person:
        data_t: tuple[str, int, bool]
        data_l: list[int]
        data_d: dict[bool, str]

    to_person = get_parser_with_no_defaults(matchers=DEFAULT_MATCHERS)(_Person)

    person = to_person(
        {
            "data_t": ["33", 33, True],
            "data_l": [1, 2, 3],
            "data_d": {True: "true", False: "false"},
        }
    )
    test.assertEqual(person.data_t, ("33", 33, True))
    test.assertEqual(person.data_l, [1, 2, 3])
    test.assertEqual(person.data_d, {True: "true", False: "false"})


@TestGetParserWithNoDefault.describe("overriding core generic validators")
def _(test: TestGetParserWithNoDefault) -> None:
    @dataclass
    class _Person:
        data_t: tuple[str, int, bool]
        data_l: list[int]
        data_d: dict[bool, str]

    for g_type in (tuple, list, dict):
        with test.subTest(f"overriding {g_type} raises"):
            with test.assertRaises(LookupError):
                _ = get_parser_with_no_defaults(unpackers={g_type: Mock()})
