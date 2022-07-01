"""matchers"""

from types import EllipsisType
from typing import Any, Iterable, get_args, get_origin

from .types import LazyMatch, NoMatch, T, TGetParse


def match_value(source: Any, target_type: type[T]) -> T | NoMatch:
    """matches source value, when it is an instance of target type"""
    if not isinstance(source, target_type):
        return NoMatch()
    return source


def match_nested(source: Any, target_type: type) -> NoMatch | LazyMatch[T]:
    """matches source value dictionary to target type"""
    if not isinstance(source, dict):
        return NoMatch()

    def resolve(get_parse: TGetParse[T]) -> T | None:
        parse = get_parse(target_type)
        return parse(source)

    return LazyMatch(resolve)


def match_iterable(source: Any, target_type: type) -> NoMatch | LazyMatch[T]:
    """matches source value to Iterables

    matches:
        - Iterable -> list
        - Iterable -> tuple
        - Iterable -> Iterable (stored as tuple)
    """
    if not isinstance(source, Iterable):
        return NoMatch()

    target_iterable = get_origin(target_type)

    if not target_iterable:
        return NoMatch()

    if target_iterable is get_origin(Iterable[T]):
        target_iterable = tuple

    if not issubclass(target_iterable, (list, tuple)):
        return NoMatch()

    (arg, *rest) = get_args(target_type)
    if len(rest) == 1 and not isinstance(rest[0], EllipsisType):
        return NoMatch()

    def resolve(get_parse: TGetParse[T]) -> T | None:
        parse = get_parse(arg)
        return target_iterable((parse(e) for e in source))  # type: ignore

    return LazyMatch(resolve)
