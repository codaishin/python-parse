"""types"""

from typing import Any, Callable, TypeVar


# pylint: disable=too-few-public-methods
class NoMatch:
    """signifies, that value could not be matched"""


class LazyMatch:
    """function decorator signifying, that further resolve is needed"""

    def __init__(
        self,
        resolve: Callable[["TGetParse"], Any | None],
    ) -> None:
        self._resolve = resolve

    def __call__(self, get_parse: "TGetParse") -> Any | None:
        """resolve with provided parse factory"""
        return self._resolve(get_parse)


T = TypeVar("T")
TGetParse = Callable[[type], Callable[[Any], Any | None]]
TMatchFunc = Callable[[Any, type], Any | NoMatch | LazyMatch]
TNestedTupleOrNoMatch = tuple[tuple[Any, ...], ...] | NoMatch
TUnpackGenericFunc = Callable[[Any, type], TNestedTupleOrNoMatch]
