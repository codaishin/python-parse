"""parse"""

from dataclasses import is_dataclass
from inspect import get_annotations
from types import EllipsisType, NoneType, UnionType
from typing import Any, Callable, Union, get_args, get_origin

from .generics_unpack import unpack_dict, unpack_list, unpack_tuple
from .matchers import (
    match_dict,
    match_list,
    match_nested,
    match_tuple,
    match_value,
)
from .types import LazyMatch, NoMatch, T, TMatchFunc, TUnpackGenericFunc

TYPE_ERROR_MSG = "'{key}' in data not compatible with '{type}'"
KEY_ERROR_MSG = "'{key}' not found in data"


DEFAULT_MATCHERS: tuple[TMatchFunc, ...] = (
    match_tuple,
    match_list,
    match_dict,
    match_nested,
    match_value,
)

CORE_GENERIC_UNPACKERS: dict[type, TUnpackGenericFunc] = {
    list: unpack_list,
    tuple: unpack_tuple,
    dict: unpack_dict,
}


def get_parser(
    *,
    matchers: tuple[TMatchFunc, ...] = (),
    unpackers: dict[type, TUnpackGenericFunc] | None = None,
) -> Callable[[type[T]], Callable[[Any], T]]:
    """Get parse factory.

    Keyword Arguments:
        matchers: Matchers used to match source value against
            target type. Matchers are used in the provided order.
            If none matched, DEFAULT_MATCHERS will be used.
        unpackers: Functions to unpack generic types for type validation.
            Generic unpackers for list, tuple and dict are always used
            and cannot be overridden.

    Returns:
        (type[T]) -> (Any) -> T:
            Parser to parse the desired type from source data

    Raises:
        TypeError: When value could not be parsed
        KeyError: When an attribute could not be found in the value
        LookupError: When a core generic unpacker is overridden
    """
    return get_parser_with_no_defaults(
        matchers=matchers + DEFAULT_MATCHERS,
        unpackers=unpackers,
    )


def get_parser_with_no_defaults(
    *,
    matchers: tuple[TMatchFunc, ...] = (),
    unpackers: dict[type, TUnpackGenericFunc] | None = None,
) -> Callable[[type[T]], Callable[[Any], T]]:
    """Get parse factory.

    Keyword Arguments:
        matchers: Matchers used to match source value against
            target type. Matchers are used in the provided order.
        unpackers: Functions to unpack generic types for type validation.
            Generic unpackers for list, tuple and dict are always used
            and cannot be overridden.

    Returns:
        (type[T]) -> (Any) -> T:
            Parser to parse the desired type from source data

    Raises:
        TypeError: When value could not be parsed
        KeyError: When an attribute could not be found in the value
        LookupError: When a core generic unpacker is overridden
    """

    _unpackers = unpackers or {}
    for key in CORE_GENERIC_UNPACKERS:
        if key in _unpackers:
            raise LookupError()
    _unpackers = _unpackers | CORE_GENERIC_UNPACKERS

    def partial_parse(target_type: type[T]) -> Callable[[Any], T]:
        parse_optional = _get_parse_factory(matchers, _unpackers)(target_type)

        def parse(value: Any) -> T:
            result = parse_optional(value)
            if result is None:
                raise TypeError()
            return result

        return parse

    return partial_parse


def _get_parse_factory(
    matchers: tuple[TMatchFunc, ...],
    unpackers: dict[type, TUnpackGenericFunc],
) -> Callable[[type[T]], Callable[[Any], T | None]]:
    def partial_parse(target_type: type[T]) -> Callable[[Any], T | None]:
        def parse(value: Any) -> T | None:
            (optional, types) = _unpack_union(target_type)

            if not isinstance(value, dict):
                return _parse(
                    types,
                    matchers,
                    unpackers,
                    value,
                    optional,
                )

            target_origin = get_origin(target_type)
            if target_origin and issubclass(target_origin, dict):
                return _parse(
                    (target_type,),
                    matchers,
                    unpackers,
                    value,
                    optional,
                )

            annotations = get_annotations(target_type)
            attributes = _parse_attributes(
                annotations,
                matchers,
                unpackers,
                value,
            )

            if optional and attributes is None:
                return None

            if is_dataclass(target_type):
                return _init_kwargs(target_type, attributes)
            return _init_and_setattr(target_type, attributes)

        return parse

    return partial_parse


_NO_MATCH: TUnpackGenericFunc = lambda _, __: NoMatch()


def _is_valid(
    parsed: Any,
    target_type: type,
    unpackers: dict[type, TUnpackGenericFunc],
) -> bool:
    if parsed is Ellipsis and isinstance(target_type, EllipsisType):
        return True

    try:
        if isinstance(parsed, target_type):
            return True
    except TypeError:
        pass

    target_origin: type | None = get_origin(target_type)
    if target_origin is None:
        return False

    unpack = unpackers.get(target_origin, _NO_MATCH)
    parsed_values = unpack(parsed, target_type)

    if isinstance(parsed_values, NoMatch):
        return False

    target_args = get_args(target_type)
    if len(target_args) != len(parsed_values):
        return False

    for values, target_arg in zip(parsed_values, target_args):
        for value in values:
            if not _is_valid(value, target_arg, unpackers):
                return False

    return True


def _parse(
    target_union_args: tuple[type, ...],
    matchers: tuple[TMatchFunc, ...],
    unpackers: dict[type, TUnpackGenericFunc],
    value: Any,
    optional: bool,
) -> Any | None:
    parsed = _parse_value(value, target_union_args, matchers, unpackers)

    if optional and parsed is None:
        return None

    if any((_is_valid(parsed, arg, unpackers) for arg in target_union_args)):
        return parsed

    raise TypeError()


def _parse_key_value(
    value: dict[Any, Any],
    key: str,
    t_key: type,
    matchers: tuple[TMatchFunc, ...],
    unpackers: dict[type, TUnpackGenericFunc],
) -> Any:
    try:
        optional, types = _unpack_union(t_key)
        value = value.get(key) if optional else value[key]
        return _parse(types, matchers, unpackers, value, optional)
    except TypeError as err:
        raise TypeError(TYPE_ERROR_MSG.format(key=key, type=t_key)) from err
    except KeyError as err:
        raise KeyError(KEY_ERROR_MSG.format(key=key)) from err


def _parse_value(
    value: Any,
    target_union_args: tuple[type, ...],
    matchers: tuple[TMatchFunc, ...],
    unpackers: dict[type, TUnpackGenericFunc],
) -> Any | None:
    for target_type in target_union_args:
        resolve = _try_matchers(matchers, value, target_type)
        if isinstance(resolve, LazyMatch):
            get_parse = _get_parse_factory(matchers, unpackers)
            return resolve(get_parse)
        if not isinstance(resolve, NoMatch):
            return resolve
    return None


def _try_matchers(
    matchers: tuple[TMatchFunc, ...],
    source_value: Any,
    target_type: type,
) -> T | NoMatch | LazyMatch:
    for match in matchers:
        result = match(source_value, target_type)
        if not isinstance(result, NoMatch):
            return result

    return NoMatch()


def _parse_attributes(
    annotations: dict[str, type],
    matchers: tuple[TMatchFunc, ...],
    unpackers: dict[type, TUnpackGenericFunc],
    data: dict[str, Any],
) -> dict[str, Any]:
    return {
        k: _parse_key_value(data, k, t, matchers, unpackers)
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
