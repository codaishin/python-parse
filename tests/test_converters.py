"""test converters"""


from unittest.mock import Mock, call

from python_parse.converters import convert_tuple
from python_parse.types import NoMatch, ResolveWithParser

from .test import UnitTests


class TestConvertToTuple(UnitTests):
    """test match_tuple"""


@TestConvertToTuple.describe("NoMatch when source no tuple")
def _(test: TestConvertToTuple) -> None:
    resolve = convert_tuple(object(), tuple[int])

    test.assertIsInstance(resolve, NoMatch)


@TestConvertToTuple.describe("NoMatch when target_type no tuple")
def _(test: TestConvertToTuple) -> None:
    resolve = convert_tuple((22,), int)

    test.assertIsInstance(resolve, NoMatch)


@TestConvertToTuple.describe("NoMatch when count mismatches")
def _(test: TestConvertToTuple) -> None:
    # come on mypy, tuple[int, str] should be compatible with type
    resolve = convert_tuple((22, 11), tuple[int, int, int])  # type: ignore

    test.assertIsInstance(resolve, NoMatch)


@TestConvertToTuple.describe("match single item LazyMatch")
def _(test: TestConvertToTuple) -> None:
    resolve = convert_tuple((2,), tuple[int])

    test.assertIsInstance(resolve, ResolveWithParser)


@TestConvertToTuple.describe("match single item result")
def _(test: TestConvertToTuple) -> None:
    resolve = convert_tuple((False,), tuple[bool])
    assert isinstance(resolve, ResolveWithParser)

    parse = Mock(side_effect=lambda v: v)
    get_parse = Mock(return_value=parse)
    result = resolve(get_parse)

    test.assertEqual(result, (False,))
    parse.assert_called_once_with(False)
    get_parse.assert_called_once_with(bool)


@TestConvertToTuple.describe("match multiple item result")
def _(test: TestConvertToTuple) -> None:

    # come on mypy, tuple[int, str] should be compatible with type
    resolve = convert_tuple((2, "44"), tuple[int, str])  # type: ignore
    assert isinstance(resolve, ResolveWithParser)

    parse = Mock(side_effect=lambda v: v)
    get_parse = Mock(return_value=parse)

    result = resolve(get_parse)
    test.assertEqual(result, (2, "44"))
    get_parse.assert_has_calls((call(int), call(str)))
    parse.assert_has_calls((call(2), call("44")))


@TestConvertToTuple.describe("match tuple with ellipsis")
def _(test: TestConvertToTuple) -> None:

    resolve = convert_tuple((2, 3, 4), tuple[int, ...])
    assert isinstance(resolve, ResolveWithParser)

    parse = Mock(side_effect=lambda v: v)
    get_parse = Mock(return_value=parse)

    result = resolve(get_parse)
    test.assertEqual(result, (2, 3, 4))
    get_parse.assert_has_calls((call(int), call(int), call(int)))
    parse.assert_has_calls((call(2), call(3), call(4)))


@TestConvertToTuple.describe("match multiple item result in list")
def _(test: TestConvertToTuple) -> None:

    # come on mypy, tuple[int, str] should be compatible with type
    resolve = convert_tuple([2, "44"], tuple[int, str])  # type: ignore
    assert isinstance(resolve, ResolveWithParser)

    parse = Mock(side_effect=lambda v: v)
    get_parse = Mock(return_value=parse)

    result = resolve(get_parse)
    test.assertEqual(result, (2, "44"))
    get_parse.assert_has_calls((call(int), call(str)))
    parse.assert_has_calls((call(2), call("44")))
