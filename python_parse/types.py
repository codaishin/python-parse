"""types"""

from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")
TGetParse = Callable[[type[T]], Callable[[Any], T | None]]
TMatchFunc = Callable[[Any, type], T | "NoMatch" | "LazyMatch[T]"]

# pylint: disable=too-few-public-methods
class NoMatch:
    """signifies, that value could not be matched"""


class LazyMatch(Generic[T]):
    """signifies, that value needs further resolve"""

    def __init__(
        self,
        resolve: Callable[[TGetParse[T]], T | None],
    ) -> None:
        self._resolve = resolve

    def resolve_with(self, get_parse: TGetParse[T]) -> T | None:
        """pass `get_parse` onto stored resolve func"""
        return self._resolve(get_parse)
