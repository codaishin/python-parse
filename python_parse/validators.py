"""validators"""


from types import EllipsisType
from typing import Any, Iterable, get_args, get_origin


def validate_iterable(parsed: Any, target_type: type) -> bool:
    """validate iterable contained types"""
    if not isinstance(parsed, Iterable):
        return False

    len_parsed = len(tuple(parsed))
    args = get_args(target_type)
    origin = get_origin(target_type)

    if origin is None:
        return False

    if len(args) == 2 and isinstance(args[1], EllipsisType):
        args = (args[0],) * len_parsed

    if issubclass(origin, list):
        args = (args[0],) * len_parsed

    if not len(args) == len_parsed:
        return False

    for arg, elem in zip(args, parsed):
        if not isinstance(elem, arg):
            return False

    return True


def validate_dict(parsed: Any, target_type: type) -> bool:
    """validate dict"""
    (t_key, t_value) = get_args(target_type)

    if not isinstance(parsed, dict):
        return False

    for key, value in parsed.items():
        if not isinstance(key, t_key):
            return False
        if not isinstance(value, t_value):
            return False
    return True
