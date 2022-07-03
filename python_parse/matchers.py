"""matchers"""

from types import EllipsisType
from typing import Any, Iterable, get_args, get_origin

from .types import LazyMatch, NoMatch, T, TGetParse


def match_value(source: Any, target_type: type[T]) -> T | NoMatch:
    """matches source value, when it is an instance of target type"""
    if not isinstance(source, target_type):
        return NoMatch()
    return source


def match_nested(source: Any, target_type: type) -> NoMatch | LazyMatch:
    """matches source value dictionary to target type"""
    if not isinstance(source, dict):
        return NoMatch()

    @LazyMatch
    def resolve(get_parse: TGetParse) -> Any | None:
        parse = get_parse(target_type)
        return parse(source)

    return resolve


def match_dict(source: Any, target_type: type) -> NoMatch | LazyMatch:
    """matches dictionary"""

    if not isinstance(source, dict):
        return NoMatch()

    origin = get_origin(target_type)
    if origin is None or not issubclass(origin, dict):
        return NoMatch()

    (t_key, t_value) = get_args(target_type)

    @LazyMatch
    def resolve(get_parser: TGetParse) -> Any | None:
        parse_key = get_parser(t_key)
        parse_value = get_parser(t_value)
        return {parse_key(k): parse_value(v) for k, v in source.items()}

    return resolve


def match_list(source: Any, target_type: type) -> NoMatch | LazyMatch:
    """matches source iterable to list"""
    if not isinstance(source, Iterable):
        return NoMatch()

    origin_type = get_origin(target_type)
    if origin_type is None or not issubclass(origin_type, list):
        return NoMatch()

    (arg,) = get_args(target_type)

    @LazyMatch
    def resolve(get_parse: TGetParse) -> Any | None:
        parse = get_parse(arg)
        return list((parse(e) for e in source))

    return resolve


def match_tuple(source: Any, target_type: type) -> NoMatch | LazyMatch:
    """match source Iterable to tuple"""

    if not isinstance(source, Iterable):
        return NoMatch()

    origin_type = get_origin(target_type)
    if origin_type is None or not issubclass(origin_type, tuple):
        return NoMatch()

    args: tuple[type, ...] = get_args(target_type)
    len_source = len(tuple(source))
    if len(args) == 2 and isinstance(args[1], EllipsisType):
        args = (args[0],) * len_source
    if len(args) != len_source:
        return NoMatch()

    @LazyMatch
    def resolve(get_parse: TGetParse) -> Any:
        return tuple((get_parse(a)(v) for v, a in zip(source, args)))

    return resolve
