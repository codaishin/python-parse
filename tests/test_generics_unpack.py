"""test generics_unpack"""

from typing import Any

from python_parse.parse import get_parser_with_no_defaults
from python_parse.types import ResolveWithParser, TParser

from .test import UnitTests


class TestGenericsUnpack(UnitTests):
    """test get_parser_with_no_default"""


@TestGenericsUnpack.describe(
    "validate_iterable not for matching tuple[int, str]"
)
def _(test: TestGenericsUnpack) -> None:
    def make_tuple(_: Any, __: type) -> ResolveWithParser:
        @ResolveWithParser
        def resolve(_: TParser) -> Any | None:
            return (1, "2")

        return resolve

    parser = get_parser_with_no_defaults(converters=(make_tuple,))
    # mypy, why? Why?!?!?!?!
    to_tuple = parser(tuple[int, int])  # type: ignore
    with test.assertRaises(TypeError):
        _ = to_tuple(object())


@TestGenericsUnpack.describe("validate_iterable for matching tuple[int, str]")
def _(test: TestGenericsUnpack) -> None:
    def make_tuple(_: Any, __: type) -> ResolveWithParser:
        @ResolveWithParser
        def resolve(_: TParser) -> Any | None:
            return (1, "2")

        return resolve

    parser = get_parser_with_no_defaults(converters=(make_tuple,))
    # mypy, why? Why?!?!?!?!
    to_tuple = parser(tuple[int, str])  # type: ignore
    result = to_tuple(object())
    test.assertEqual(result, (1, "2"))


@TestGenericsUnpack.describe(
    "validate_iterable for matching tuple[int, Ellipsis]"
)
def _(test: TestGenericsUnpack) -> None:
    def make_tuple(_: Any, __: type) -> ResolveWithParser:
        @ResolveWithParser
        def resolve(_: TParser) -> Any | None:
            return (1, 2, 3, 4)

        return resolve

    parser = get_parser_with_no_defaults(converters=(make_tuple,))
    to_tuple = parser(tuple[int, ...])
    result = to_tuple(object())
    test.assertEqual(result, (1, 2, 3, 4))


@TestGenericsUnpack.describe("validate_iterable for matching list[int]")
def _(test: TestGenericsUnpack) -> None:
    def make_list(_: Any, __: type) -> ResolveWithParser:
        @ResolveWithParser
        def resolve(_: TParser) -> Any | None:
            return [1, 2, 3, 4]

        return resolve

    parser = get_parser_with_no_defaults(converters=(make_list,))
    to_tuple = parser(list[int])
    result = to_tuple(object())
    test.assertEqual(result, [1, 2, 3, 4])


@TestGenericsUnpack.describe(
    "validate_iterable for not matching dict[str, int]"
)
def _(test: TestGenericsUnpack) -> None:
    def make_list(_: Any, __: type) -> ResolveWithParser:
        @ResolveWithParser
        def resolve(_: TParser) -> Any | None:
            return {False: "aaaa"}

        return resolve

    parser = get_parser_with_no_defaults(converters=(make_list,))
    to_tuple = parser(dict[str, int])
    with test.assertRaises(TypeError):
        __ = to_tuple(object())


@TestGenericsUnpack.describe("validate_iterable for matching dict[str, int]")
def _(test: TestGenericsUnpack) -> None:
    def make_list(_: Any, __: type) -> ResolveWithParser:
        @ResolveWithParser
        def resolve(_: TParser) -> Any | None:
            return {"key": 40, "other key": 2}

        return resolve

    parser = get_parser_with_no_defaults(converters=(make_list,))
    to_tuple = parser(dict[str, int])
    result = to_tuple(object())
    test.assertEqual(result, {"key": 40, "other key": 2})
