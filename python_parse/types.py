"""types"""

from typing import Any, Callable, TypeVar


# pylint: disable=too-few-public-methods
class NoMatch:
    """signifies, that value could not be matched"""


class ResolveWithParser:
    """
    function decorator signifying, that further resolve with a parser is
    needed
    """

    def __init__(
        self,
        resolve: Callable[["TParser"], Any | None],
    ) -> None:
        self._resolve = resolve

    def __call__(self, parser: "TParser") -> Any | None:
        """resolve with provided parse factory"""
        return self._resolve(parser)


T = TypeVar("T")
TParser = Callable[[type], Callable[[Any], Any | None]]
TConvertFunc = Callable[[Any, type], Any | NoMatch | ResolveWithParser]
TNestedTupleOrNoMatch = tuple[tuple[Any, ...], ...] | NoMatch
TUnpackGenericFunc = Callable[[Any, type], TNestedTupleOrNoMatch]
