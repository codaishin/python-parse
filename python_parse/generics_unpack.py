"""generics unpack"""


from types import EllipsisType
from typing import Any, Iterable, get_args, get_origin

from python_parse.types import NoMatch, TNestedTupleOrNoMatch


def unpack_iterable(parsed: Any, target_type: type) -> TNestedTupleOrNoMatch:
    """get elements of Iterable"""
    if not isinstance(parsed, Iterable):
        return NoMatch()

    parsed_tuple = tuple(parsed)
    origin = get_origin(target_type) or target_type
    if issubclass(origin, list):
        return (parsed_tuple,)

    if issubclass(origin, tuple):
        args: tuple[type, ...] = get_args(target_type)
        if len(args) == 2 and isinstance(args[1], EllipsisType):
            return (parsed_tuple, (...,))

        if len(args) == len(parsed_tuple):
            return tuple(((v,) for v in parsed_tuple))

    return NoMatch()


def unpack_dict(parsed: Any, _: type) -> TNestedTupleOrNoMatch:
    """get keys and values of parsed dict"""
    if not isinstance(parsed, dict):
        return NoMatch()

    return (tuple(parsed.keys()), tuple(parsed.values()))
