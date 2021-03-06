"""converters"""

from types import EllipsisType
from typing import Any, Iterable, get_args, get_origin

from .types import NoMatch, ResolveWithParser, T, TParser


def convert_value(source: Any, target_type: type[T]) -> T | NoMatch:
    """return source value, when it is an instance of target type"""
    if not isinstance(source, target_type):
        return NoMatch()
    return source


def convert_nested(
    source: Any,
    target_type: type,
) -> NoMatch | ResolveWithParser:
    """convert source value dictionary to target type"""
    if not isinstance(source, dict):
        return NoMatch()

    @ResolveWithParser
    def resolve(parser: TParser) -> Any | None:
        parse = parser(target_type)
        return parse(source)

    return resolve


def convert_dict(
    source: Any,
    target_type: type,
) -> NoMatch | ResolveWithParser:
    """convert dictionary"""

    if not isinstance(source, dict):
        return NoMatch()

    origin = get_origin(target_type)
    if origin is None or not issubclass(origin, dict):
        return NoMatch()

    (t_key, t_value) = get_args(target_type)

    @ResolveWithParser
    def resolve(parser: TParser) -> Any | None:
        parse_key = parser(t_key)
        parse_value = parser(t_value)
        return {parse_key(k): parse_value(v) for k, v in source.items()}

    return resolve


def convert_list(
    source: Any,
    target_type: type,
) -> NoMatch | ResolveWithParser:
    """convert source iterable to list"""
    if not isinstance(source, Iterable):
        return NoMatch()

    origin_type = get_origin(target_type)
    if origin_type is None or not issubclass(origin_type, list):
        return NoMatch()

    (arg,) = get_args(target_type)

    @ResolveWithParser
    def resolve(parser: TParser) -> Any | None:
        parse = parser(arg)
        return list((parse(e) for e in source))

    return resolve


def convert_tuple(
    source: Any,
    target_type: type,
) -> NoMatch | ResolveWithParser:
    """convert source Iterable to tuple"""

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

    @ResolveWithParser
    def resolve(parser: TParser) -> Any:
        return tuple((parser(a)(v) for v, a in zip(source, args)))

    return resolve
