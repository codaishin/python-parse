"""test validators"""

from typing import Any

from python_parse.parse import get_parser_with_no_defaults
from python_parse.types import LazyMatch, TGetParse
from python_parse.validators import validate_dict, validate_iterable

from .test import UnitTests


class TestValidators(UnitTests):
    """test get_parser_with_no_default"""


@TestValidators.describe("validate_iterable not for matching tuple[int, str]")
def _(test: TestValidators) -> None:
    def make_tuple(_: Any, __: type) -> LazyMatch:
        @LazyMatch
        def resolve(_: TGetParse) -> Any | None:
            return (1, "2")

        return resolve

    parser = get_parser_with_no_defaults(
        matchers=(make_tuple,),
        generic_validators={tuple: validate_iterable},
    )
    # mypy, why? Why?!?!?!?!
    to_tuple = parser(tuple[int, int])  # type: ignore
    with test.assertRaises(TypeError):
        _ = to_tuple(object())


@TestValidators.describe("validate_iterable for matching tuple[int, str]")
def _(test: TestValidators) -> None:
    def make_tuple(_: Any, __: type) -> LazyMatch:
        @LazyMatch
        def resolve(_: TGetParse) -> Any | None:
            return (1, "2")

        return resolve

    parser = get_parser_with_no_defaults(
        matchers=(make_tuple,),
        generic_validators={tuple: validate_iterable},
    )
    # mypy, why? Why?!?!?!?!
    to_tuple = parser(tuple[int, str])  # type: ignore
    result = to_tuple(object())
    test.assertEqual(result, (1, "2"))


@TestValidators.describe("validate_iterable for matching tuple[int, Ellipsis]")
def _(test: TestValidators) -> None:
    def make_tuple(_: Any, __: type) -> LazyMatch:
        @LazyMatch
        def resolve(_: TGetParse) -> Any | None:
            return (1, 2, 3, 4)

        return resolve

    parser = get_parser_with_no_defaults(
        matchers=(make_tuple,),
        generic_validators={tuple: validate_iterable},
    )
    to_tuple = parser(tuple[int, ...])
    result = to_tuple(object())
    test.assertEqual(result, (1, 2, 3, 4))


@TestValidators.describe("validate_iterable for matching list[int]")
def _(test: TestValidators) -> None:
    def make_list(_: Any, __: type) -> LazyMatch:
        @LazyMatch
        def resolve(_: TGetParse) -> Any | None:
            return [1, 2, 3, 4]

        return resolve

    parser = get_parser_with_no_defaults(
        matchers=(make_list,),
        generic_validators={list: validate_iterable},
    )
    to_tuple = parser(list[int])
    result = to_tuple(object())
    test.assertEqual(result, [1, 2, 3, 4])


@TestValidators.describe("validate_iterable for not matching dict[str, int]")
def _(test: TestValidators) -> None:
    def make_list(_: Any, __: type) -> LazyMatch:
        @LazyMatch
        def resolve(_: TGetParse) -> Any | None:
            return {False: "aaaa"}

        return resolve

    parser = get_parser_with_no_defaults(
        matchers=(make_list,),
        generic_validators={dict: validate_dict},
    )
    to_tuple = parser(dict[str, int])
    with test.assertRaises(TypeError):
        __ = to_tuple(object())


@TestValidators.describe("validate_iterable for matching dict[str, int]")
def _(test: TestValidators) -> None:
    def make_list(_: Any, __: type) -> LazyMatch:
        @LazyMatch
        def resolve(_: TGetParse) -> Any | None:
            return {"key": 40, "other key": 2}

        return resolve

    parser = get_parser_with_no_defaults(
        matchers=(make_list,),
        generic_validators={dict: validate_dict},
    )
    to_tuple = parser(dict[str, int])
    result = to_tuple(object())
    test.assertEqual(result, {"key": 40, "other key": 2})
