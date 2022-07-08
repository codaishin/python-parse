"""generics unpack"""


from types import EllipsisType
from typing import Any, Iterable, get_args

from python_parse.types import NoMatch, TNestedTupleOrNoMatch


def unpack_list(parsed: Any, _: type) -> TNestedTupleOrNoMatch:
    """get elements of list"""
    if not isinstance(parsed, Iterable):
        return NoMatch()

    parsed_tuple = tuple(parsed)
    return (parsed_tuple,)


def unpack_tuple(parsed: Any, target_type: type) -> TNestedTupleOrNoMatch:
    """unpack elements of tuple"""
    args: tuple[type, ...] = get_args(target_type)
    parsed_tuple = tuple(parsed)
    if len(args) == 2 and isinstance(args[1], EllipsisType):
        return (parsed_tuple, (...,))

    return tuple(((v,) for v in parsed_tuple))


def unpack_dict(parsed: Any, _: type) -> TNestedTupleOrNoMatch:
    """get keys and values of parsed dict"""
    if not isinstance(parsed, dict):
        return NoMatch()

    return (tuple(parsed.keys()), tuple(parsed.values()))
