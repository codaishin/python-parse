"""parse"""

from dataclasses import is_dataclass
from inspect import get_annotations
from types import NoneType
from typing import Any, Callable, Union, get_args, get_origin

from .matchers import match_dict, match_iterable, match_nested, match_value
from .types import LazyMatch, NoMatch, T, TMatchFunc

TYPE_ERROR_MSG = "'{key}' in data not compatible with '{type}'"
KEY_ERROR_MSG = "'{key}' not found in data"


DEFAULT_MATCHERS: tuple[TMatchFunc[Any], ...] = (
    match_iterable,
    match_dict,
    match_nested,
    match_value,
)


def get_parser(
    *matchers: TMatchFunc[Any],
) -> Callable[[type[T]], Callable[[Any], T | None]]:
    """
    Get parse factory that uses the provided matchers and then
    `DEFAULT_MATCHERS`.
    Matchers will be used in order until one matches.

    Raises:
        TypeError: When no matcher matched
    """
    return get_parser_with_no_defaults(*(matchers + DEFAULT_MATCHERS))


def get_parser_with_no_defaults(
    *matchers: TMatchFunc[Any],
) -> Callable[[type[T]], Callable[[Any], T | None]]:
    """
    Get parse factory that uses the provided matchers.
    Matchers will be used in order until one matches.

    Raises:
        TypeError: When no matcher matched
    """

    def partial_parse(target_type: type[T]) -> Callable[[Any], T | None]:
        def parse(value: Any) -> T | None:
            return _parse(matchers, target_type, value)

        return parse

    return partial_parse


def _parse(
    matchers: tuple[TMatchFunc[Any], ...],
    target_type: type[T],
    data: Any,
) -> T | None:
    (optional, target_type) = _unpack_union(target_type)
    if not isinstance(data, dict):
        return _parse_flat(target_type, matchers, data, optional)

    target_origin = get_origin(target_type) or target_type
    if issubclass(target_origin, dict):
        return _parse_flat(target_type, matchers, data, optional)

    annotations = get_annotations(target_type)
    attributes = _get_attributes(annotations, matchers, data)

    if optional and attributes is None:
        return None

    if is_dataclass(target_type):
        return _init_kwargs(target_type, attributes)
    return _init_and_setattr(target_type, attributes)


def _parse_key(
    data: dict[Any, Any],
    key: str,
    t_key: type,
    matchers: tuple[TMatchFunc[Any], ...],
) -> Any:
    try:
        optional, t_key = _unpack_union(t_key)
        value = data.get(key) if optional else data[key]
        return _parse_flat(t_key, matchers, value, optional)
    except TypeError as err:
        raise TypeError(TYPE_ERROR_MSG.format(key=key, type=t_key)) from err
    except KeyError as err:
        raise KeyError(KEY_ERROR_MSG.format(key=key)) from err


def _parse_flat(
    target_type: type[T],
    matchers: tuple[TMatchFunc[Any], ...],
    data: Any,
    optional: bool,
) -> T | None:
    parsed = _parse_value(data, target_type, matchers)

    if optional and parsed is None:
        return None

    target_origin: type[T] = get_origin(target_type) or target_type
    if isinstance(parsed, target_origin):
        return parsed

    raise TypeError()


def _parse_value(
    value: Any,
    t_key: type[T],
    matchers: tuple[TMatchFunc[Any], ...],
) -> T | None:
    resolve = _try_matchers(matchers, value, t_key)
    if isinstance(resolve, NoMatch):
        return None
    if isinstance(resolve, LazyMatch):
        get_parse = get_parser_with_no_defaults(*matchers)
        return resolve(get_parse)
    return resolve


def _try_matchers(
    value_parsers: tuple[TMatchFunc[Any], ...],
    source_value: Any,
    target_type: type[T],
) -> T | NoMatch | LazyMatch[T]:
    for parser in value_parsers:
        result = parser(source_value, target_type)
        if not isinstance(result, NoMatch):
            return result

    return NoMatch()


def _get_attributes(
    annotations: dict[str, type],
    value_parsers: tuple[TMatchFunc[Any], ...],
    data: dict[str, Any],
) -> dict[str, Any]:
    return {
        key: _parse_key(data, key, t_key, value_parsers)
        for key, t_key in annotations.items()
    }


def _unpack_union(target_type: type) -> tuple[bool, type]:
    if get_origin(target_type) is Union:
        (target_type,) = (
            t for t in get_args(target_type) if t is not NoneType
        )
        return True, target_type
    return False, target_type


def _init_kwargs(cls: type[T], attributes: Any) -> T:
    return cls(**attributes)


def _init_and_setattr(cls: type[T], attributes: dict[str, Any]) -> T:
    obj = cls()
    for key, value in attributes.items():
        setattr(obj, key, value)
    return obj
