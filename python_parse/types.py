"""types"""

from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")
TGetParse = Callable[[type[T]], Callable[[Any], T | None]]
TMatchFunc = Callable[[Any, type], T | "NoMatch" | "LazyMatch[T]"]

# pylint: disable=too-few-public-methods
class NoMatch:
    """signifies, that value could not be matched"""


class LazyMatch(Generic[T]):
    """function decorator signifying, that further resolve is needed"""

    def __init__(
        self,
        resolve: Callable[[TGetParse[T]], T | None],
    ) -> None:
        self._resolve = resolve

    def __call__(self, get_parse: TGetParse[T]) -> T | None:
        """resolve with provided parse factory"""
        return self._resolve(get_parse)
