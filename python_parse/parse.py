"""parse"""

from dataclasses import is_dataclass
from functools import reduce
from inspect import get_annotations
from types import EllipsisType, NoneType, UnionType
from typing import Any, Callable, Union, get_args, get_origin

from .converters import (
    convert_dict,
    convert_list,
    convert_nested,
    convert_tuple,
    convert_value,
)
from .generics_unpack import unpack_dict, unpack_to_list, unpack_to_tuple
from .types import (
    NoMatch,
    ResolveWithParser,
    T,
    TConvertFunc,
    TNestedTupleOrNoMatch,
    TUnpackGenericFunc,
)

TYPE_ERROR_MSG = "'{key}' in data not compatible with '{type}'"
KEY_ERROR_MSG = "'{key}' not found in data"


DEFAULT_CONVERTERS: tuple[TConvertFunc, ...] = (
    convert_tuple,
    convert_list,
    convert_dict,
    convert_nested,
    convert_value,
)

CORE_UNPACKERS: tuple[TUnpackGenericFunc, ...] = (
    unpack_to_list,
    unpack_to_tuple,
    unpack_dict,
)


def get_parser(
    *,
    converters: tuple[TConvertFunc, ...] = (),
    unpackers: tuple[TUnpackGenericFunc, ...] = (),
) -> Callable[[type[T]], Callable[[Any], T]]:
    """Get parse factory.

    Keyword Arguments:
        converters: Converters used to convert source value to target
            type. Converters are used in the provided order.
            If no converter could be applied, DEFAULT_CONVERTERS will
            be used.
        unpackers: Functions to unpack generic types for type validation.
            Generic unpackers for list, tuple and dict are always used
            and cannot be overridden.

    Returns:
        (type[T]) -> (Any) -> T:
            Parser to parse the desired type from source data

    Raises:
        TypeError: When value could not be parsed
        KeyError: When an attribute could not be found in the value
    """
    return get_parser_with_no_defaults(
        converters=converters + DEFAULT_CONVERTERS,
        unpackers=unpackers,
    )


def get_parser_with_no_defaults(
    *,
    converters: tuple[TConvertFunc, ...] = (),
    unpackers: tuple[TUnpackGenericFunc, ...] = (),
) -> Callable[[type[T]], Callable[[Any], T]]:
    """Get parse factory.

    Keyword Arguments:
        converters: Converters used to convert source value to target
            type. Converters are used in the provided order.
        unpackers: Functions to unpack generic types for type validation.
            Generic unpackers for list, tuple and dict are always used
            and cannot be overridden.

    Returns:
        (type[T]) -> (Any) -> T:
            Parser to parse the desired type from source data

    Raises:
        TypeError: When value could not be parsed
        KeyError: When an attribute could not be found in the value
    """

    def partial_parse(target_type: type[T]) -> Callable[[Any], T]:
        parser = _get_parser(converters, CORE_UNPACKERS + unpackers)
        parse_optional = parser(target_type)

        def parse_required(value: Any) -> T:
            result = parse_optional(value)
            if result is None:
                raise TypeError()
            return result

        return parse_required

    return partial_parse


def _get_parser(
    converters: tuple[TConvertFunc, ...],
    unpackers: tuple[TUnpackGenericFunc, ...],
) -> Callable[[type[T]], Callable[[Any], T | None]]:
    def partial_parse(target_type: type[T]) -> Callable[[Any], T | None]:
        def parse(value: Any) -> T | None:
            (optional, types) = _unpack_union(target_type)
            if not isinstance(value, dict):
                return _parse(value, types, optional, converters, unpackers)

            target_origin = get_origin(target_type)
            types = (target_type,)
            if target_origin and issubclass(target_origin, dict):
                return _parse(value, types, optional, converters, unpackers)

            annotations = get_annotations(target_type)
            attributes = _parse_attributes(
                value,
                annotations,
                converters,
                unpackers,
            )

            if optional and attributes is None:
                return None

            if is_dataclass(target_type):
                return _init_kwargs(target_type, attributes)
            return _init_and_setattr(target_type, attributes)

        return parse

    return partial_parse


def _isinstance(value: Any, target_type: type) -> bool:
    try:
        return isinstance(value, target_type)
    except TypeError:
        return value is Ellipsis and isinstance(target_type, EllipsisType)


def _unpack_values(
    value: Any,
    target_type: type,
) -> Callable[
    [TNestedTupleOrNoMatch, TUnpackGenericFunc],
    TNestedTupleOrNoMatch,
]:
    def unpack(
        result: TNestedTupleOrNoMatch,
        unpacker: TUnpackGenericFunc,
    ) -> TNestedTupleOrNoMatch:
        if isinstance(result, NoMatch):
            return unpacker(value, target_type)
        return result

    return unpack


def _is_valid(
    value: Any,
    target_type: type,
    unpackers: tuple[TUnpackGenericFunc, ...],
) -> bool:
    if _isinstance(value, target_type):
        return True

    target_origin: type | None = get_origin(target_type)
    if target_origin is None:
        return False

    unpack = _unpack_values(value, target_type)
    elements_arg_groups: TNestedTupleOrNoMatch = NoMatch()
    elements_arg_groups = reduce(unpack, unpackers, elements_arg_groups)

    if isinstance(elements_arg_groups, NoMatch):
        return False

    target_args = get_args(target_type)
    if len(target_args) != len(elements_arg_groups):
        return False

    for elements_group, target_arg in zip(elements_arg_groups, target_args):
        for element in elements_group:
            if not _is_valid(element, target_arg, unpackers):
                return False

    return True


def _parse(
    value: Any,
    target_union_args: tuple[type, ...],
    optional: bool,
    converters: tuple[TConvertFunc, ...],
    unpackers: tuple[TUnpackGenericFunc, ...],
) -> Any | None:
    parsed = _parse_value(value, target_union_args, converters, unpackers)

    if optional and parsed is None:
        return None

    if any((_is_valid(parsed, arg, unpackers) for arg in target_union_args)):
        return parsed

    raise TypeError()


def _parse_key_value(
    value: dict[Any, Any],
    key: str,
    t_key: type,
    converters: tuple[TConvertFunc, ...],
    unpackers: tuple[TUnpackGenericFunc, ...],
) -> Any:
    try:
        optional, types = _unpack_union(t_key)
        value = value.get(key) if optional else value[key]
        return _parse(value, types, optional, converters, unpackers)
    except TypeError as err:
        raise TypeError(TYPE_ERROR_MSG.format(key=key, type=t_key)) from err
    except KeyError as err:
        raise KeyError(KEY_ERROR_MSG.format(key=key)) from err


def _parse_value(
    value: Any,
    target_union_args: tuple[type, ...],
    converters: tuple[TConvertFunc, ...],
    unpackers: tuple[TUnpackGenericFunc, ...],
) -> Any | None:
    for target_type in target_union_args:
        resolve = _try_converters(value, target_type, converters)
        if isinstance(resolve, ResolveWithParser):
            parser = _get_parser(converters, unpackers)
            return resolve(parser)
        if not isinstance(resolve, NoMatch):
            return resolve
    return None


def _try_converters(
    value: Any,
    target_type: type,
    converters: tuple[TConvertFunc, ...],
) -> T | NoMatch | ResolveWithParser:
    for convert in converters:
        result = convert(value, target_type)
        if not isinstance(result, NoMatch):
            return result

    return NoMatch()


def _parse_attributes(
    value: dict[str, Any],
    annotations: dict[str, type],
    converters: tuple[TConvertFunc, ...],
    unpackers: tuple[TUnpackGenericFunc, ...],
) -> dict[str, Any]:
    return {
        k: _parse_key_value(value, k, t, converters, unpackers)
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
