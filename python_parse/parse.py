"""parse"""

from dataclasses import is_dataclass
from inspect import get_annotations
from types import NoneType, UnionType
from typing import Any, Callable, Union, get_args, get_origin

from .matchers import (
    match_dict,
    match_list,
    match_nested,
    match_tuple,
    match_value,
)
from .types import LazyMatch, NoMatch, T, TMatchFunc

TYPE_ERROR_MSG = "'{key}' in data not compatible with '{type}'"
KEY_ERROR_MSG = "'{key}' not found in data"


DEFAULT_MATCHERS: tuple[TMatchFunc, ...] = (
    match_tuple,
    match_list,
    match_dict,
    match_nested,
    match_value,
)


def get_parser(
    *matchers: TMatchFunc,
) -> Callable[[type[T]], Callable[[Any], T]]:
    """
    Get parse factory that uses the provided matchers and then
    `DEFAULT_MATCHERS`.
    Matchers will be used in order until one matches.

    Raises:
        TypeError: When value could not be parsed
    """
    return get_parser_with_no_defaults(*(matchers + DEFAULT_MATCHERS))


def get_parser_with_no_defaults(
    *matchers: TMatchFunc,
) -> Callable[[type[T]], Callable[[Any], T]]:
    """
    Get parse factory that uses the provided matchers.
    Matchers will be used in order until one matches.

    Raises:
        TypeError: When value could not be parsed
    """

    def partial_parse(target_type: type[T]) -> Callable[[Any], T]:
        parse_optional = _get_parse_factory(matchers)(target_type)

        def parse(value: Any) -> T:
            result = parse_optional(value)
            if result is None:
                raise TypeError()
            return result

        return parse

    return partial_parse


def _get_parse_factory(
    matchers: tuple[TMatchFunc, ...]
) -> Callable[[type[T]], Callable[[Any], T | None]]:
    def partial_parse(target_type: type[T]) -> Callable[[Any], T | None]:
        def parse(value: Any) -> T | None:
            (optional, types) = _unpack_union(target_type)

            if not isinstance(value, dict):
                return _parse(types, matchers, value, optional)

            target_origin = get_origin(target_type)
            if target_origin and issubclass(target_origin, dict):
                return _parse((target_type,), matchers, value, optional)

            annotations = get_annotations(target_type)
            attributes = _parse_attributes(annotations, matchers, value)

            if optional and attributes is None:
                return None

            if is_dataclass(target_type):
                return _init_kwargs(target_type, attributes)
            return _init_and_setattr(target_type, attributes)

        return parse

    return partial_parse


def _parse(
    target_types: tuple[type[T], ...],
    matchers: tuple[TMatchFunc, ...],
    value: Any,
    optional: bool,
) -> T | None:
    parsed = _parse_value(value, target_types, matchers)

    if optional and parsed is None:
        return None

    target_origin: tuple[type[T], ...] = tuple(
        (get_origin(t) or t for t in target_types)
    )
    if isinstance(parsed, target_origin):
        return parsed

    raise TypeError()


def _parse_key_value(
    value: dict[Any, Any],
    key: str,
    t_key: type,
    matchers: tuple[TMatchFunc, ...],
) -> Any:
    try:
        optional, types = _unpack_union(t_key)
        value = value.get(key) if optional else value[key]
        return _parse(types, matchers, value, optional)
    except TypeError as err:
        raise TypeError(TYPE_ERROR_MSG.format(key=key, type=t_key)) from err
    except KeyError as err:
        raise KeyError(KEY_ERROR_MSG.format(key=key)) from err


def _parse_value(
    value: Any,
    target_types: tuple[type[T], ...],
    matchers: tuple[TMatchFunc, ...],
) -> T | None:
    for target_type in target_types:
        resolve = _try_matchers(matchers, value, target_type)
        if isinstance(resolve, LazyMatch):
            get_parse = _get_parse_factory(matchers)
            return resolve(get_parse)
        if not isinstance(resolve, NoMatch):
            return resolve
    return None


def _try_matchers(
    value_parsers: tuple[TMatchFunc, ...],
    source_value: Any,
    target_type: type,
) -> T | NoMatch | LazyMatch:
    for parser in value_parsers:
        result = parser(source_value, target_type)
        if not isinstance(result, NoMatch):
            return result

    return NoMatch()


def _parse_attributes(
    annotations: dict[str, type],
    value_parsers: tuple[TMatchFunc, ...],
    data: dict[str, Any],
) -> dict[str, Any]:
    return {
        k: _parse_key_value(data, k, t, value_parsers)
        for k, t in annotations.items()
    }


def _unpack_union(target_type: type) -> tuple[bool, tuple[type, ...]]:
    origin = get_origin(target_type)
    if origin is Union or origin is UnionType:
        union_args = get_args(target_type)
        optional = NoneType in union_args
        return optional, tuple((a for a in union_args if a is not NoneType))
    return False, (target_type,)


def _init_kwargs(cls: type[T], attributes: Any) -> T:
    return cls(**attributes)


def _init_and_setattr(cls: type[T], attributes: dict[str, Any]) -> T:
    obj = cls()
    for key, value in attributes.items():
        setattr(obj, key, value)
    return obj
