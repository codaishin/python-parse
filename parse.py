"""parse"""

from dataclasses import is_dataclass
from inspect import get_annotations
from types import NoneType
from typing import (
    Any,
    Callable,
    Iterable,
    TypeVar,
    Union,
    get_args,
    get_origin,
)


# pylint: disable=too-few-public-methods
class NoMatch:
    """signifies, that value could not be matched"""


T = TypeVar("T")
TTarget = TypeVar("TTarget")
TSource = TypeVar("TSource")
TParseFuncMatch = Callable[[Any, type[T]], T | NoMatch]

TYPE_ERROR_MSG = "'{key}' in data not compatible with '{type}'"
KEY_ERROR_MSG = "'{key}' not found in data"


def match_subtype(source_value: Any, target_type: type[Any]) -> Any | NoMatch:
    """matches target type"""
    if not isinstance(source_value, target_type):
        return NoMatch()
    return source_value


DEFAULT_VALUE_PARSERS = (match_subtype,)


def _init_and_setattr(cls: type[T], attributes: dict[str, Any]) -> T:
    obj = cls()
    for key, value in attributes.items():
        setattr(obj, key, value)
    return obj


def _init_kwargs(cls: type[T], attributes: Any) -> T:
    return cls(**attributes)


def _is_iterable_candidate(t_key: Any, value: Any) -> bool:
    return (
        t_key is not str
        and not isinstance(value, str)
        and isinstance(value, Iterable)
    )


def _origin(value: Any) -> Any:
    return get_origin(value) or value


def _is_iterable(t_key: Any, value: Any, *assert_types: Any) -> bool:
    if not _is_iterable_candidate(t_key, value):
        return False
    for assert_type in assert_types:
        if _origin(t_key) is _origin(assert_type):
            return True
    return False


def _apply_parsers(
    value_parsers: tuple[TParseFuncMatch[Any], ...],
    source_value: Any,
    target_type: type[Any],
) -> Any | NoMatch:
    for parser in value_parsers:
        result = parser(source_value, target_type)
        if not isinstance(result, NoMatch):
            return result

    return NoMatch()


def _parse_value(
    value: Any,
    t_key: Any,
    value_parsers: tuple[TParseFuncMatch[Any], ...],
) -> Any:
    parse: Callable[[Any], Any]
    if _is_iterable(t_key, value, list):
        (t_key,) = get_args(t_key)
        parse = get_parser_no_defaults(*value_parsers)(t_key)
        return [parse(e) for e in value]
    if _is_iterable(t_key, value, tuple, Iterable):
        (t_key, *_) = get_args(t_key)
        parse = get_parser_no_defaults(*value_parsers)(t_key)
        return tuple((parse(e) for e in value))
    if isinstance(value, dict):
        parse = get_parser_no_defaults(*value_parsers)(t_key)
        return parse(value)
    if isinstance(value, (list, tuple)) and len(value) == 1:
        parse = get_parser_no_defaults(*value_parsers)(t_key)
        return parse(value[0])
    result = _apply_parsers(value_parsers, value, t_key)
    if isinstance(result, NoMatch):
        return None
    return result


def _parse_key(
    data: dict[Any, Any],
    key: str,
    t_key: type,
    value_parsers: tuple[TParseFuncMatch[Any], ...],
) -> Any:
    try:
        t_key, optional = _get_optional_or_orig(t_key)
        value = data.get(key) if optional else data[key]
        return _parse_flat(t_key, value_parsers, value, optional)
    except TypeError as err:
        raise TypeError(TYPE_ERROR_MSG.format(key=key, type=t_key)) from err
    except KeyError as err:
        raise KeyError(KEY_ERROR_MSG.format(key=key)) from err


def _get_attributes(
    annotations: dict[str, type],
    sub_parsers: tuple[TParseFuncMatch[Any], ...],
    data: dict[str, Any],
) -> dict[str, Any]:
    return {
        key: _parse_key(data, key, t_key, sub_parsers)
        for key, t_key in annotations.items()
    }


def _parse_flat(
    target_type: type[T],
    value_parsers: tuple[TParseFuncMatch[Any], ...],
    data: Any,
    optional: bool,
) -> T | None:
    parsed = _parse_value(data, target_type, value_parsers)

    if optional and parsed is None:
        return None

    target_origin: type[T] = _origin(target_type)
    if isinstance(parsed, target_origin):
        return parsed

    raise TypeError()


def _get_optional_or_orig(_type: type) -> tuple[type, bool]:
    if _origin(_type) is Union:
        (_type,) = (t for t in get_args(_type) if t is not NoneType)
        return _type, True
    return _type, False


def _parse(
    value_parsers: tuple[TParseFuncMatch[Any], ...],
    target_type: type[T],
    data: Any,
) -> T | None:
    (target_type, optional) = _get_optional_or_orig(target_type)
    if not isinstance(data, dict):
        return _parse_flat(target_type, value_parsers, data, optional)

    annotations = get_annotations(target_type)
    attributes = _get_attributes(annotations, value_parsers, data)

    if optional and attributes is None:
        return None

    if is_dataclass(target_type):
        return _init_kwargs(target_type, attributes)
    return _init_and_setattr(target_type, attributes)


def get_parser_no_defaults(
    *value_parsers: TParseFuncMatch[Any],
) -> Callable[[type[T]], Callable[[Any], T | None]]:
    """get parser func that uses the provided value parsers"""

    def partial_parse(target_type: type[T]) -> Callable[[Any], T | None]:
        def parse(value: Any) -> T | None:
            return _parse(value_parsers, target_type, value)

        return parse

    return partial_parse


def get_parser(
    *value_parsers: TParseFuncMatch[Any],
) -> Callable[[type[T]], Callable[[Any], T | None]]:
    """
    get parser func which always attempts to use `DEFAULT_VALUE_PARSERS`
    when provided value parsers did not match
    """
    return get_parser_no_defaults(*(value_parsers + DEFAULT_VALUE_PARSERS))
