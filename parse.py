"""parse"""

from dataclasses import is_dataclass
from inspect import get_annotations
from types import EllipsisType, NoneType
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

T = TypeVar("T")
TParseFunc = Callable[[Any, type], T | "NoMatch" | "LazyMatch[T]"]
TGetParse = Callable[[type[T]], Callable[[Any], T | None]]

# pylint: disable=too-few-public-methods
class NoMatch:
    """signifies, that value could not be matched"""


class LazyMatch(Generic[T]):
    """signifies, that value needs further resolve"""

    def __init__(
        self,
        resolve: Callable[[TGetParse[T]], T | None],
    ) -> None:
        self._resolve = resolve

    def resolve_with(self, get_parse: TGetParse[T]) -> T | None:
        """pass `get_parse` onto stored resolve func"""
        return self._resolve(get_parse)


TYPE_ERROR_MSG = "'{key}' in data not compatible with '{type}'"
KEY_ERROR_MSG = "'{key}' not found in data"


def match_value(source_value: Any, target_type: type[T]) -> T | NoMatch:
    """matches target type with source value type"""
    if not isinstance(source_value, target_type):
        return NoMatch()
    return source_value


def match_dict(source_value: Any, target_type: type) -> NoMatch | LazyMatch[T]:
    """match dict to a nested type"""
    if not isinstance(source_value, dict):
        return NoMatch()

    def resolve(get_parse: TGetParse[T]) -> T | None:
        parse = get_parse(target_type)
        return parse(source_value)

    return LazyMatch(resolve)


def match_iter(source_value: Any, target_type: type) -> NoMatch | LazyMatch[T]:
    """match iterables

    matches:
        - Iterable -> list
        - Iterable -> tuple
        - Iterable -> Iterable (stored as tuple)
    """
    if not isinstance(source_value, Iterable):
        return NoMatch()

    target_iterable = get_origin(target_type)

    if not target_iterable:
        return NoMatch()

    if target_iterable is get_origin(Iterable[Any]):
        target_iterable = tuple

    if not issubclass(target_iterable, (list, tuple)):
        return NoMatch()

    (arg, *rest) = get_args(target_type)
    if len(rest) == 1 and not isinstance(rest[0], EllipsisType):
        return NoMatch()

    def resolve(get_parse: TGetParse[T]) -> T | None:
        parse = get_parse(arg)
        return target_iterable((parse(e) for e in source_value))  # type: ignore

    return LazyMatch(resolve)


DEFAULT_VALUE_PARSERS: tuple[TParseFunc[Any], ...] = (
    match_iter,
    match_dict,
    match_value,
)


def _init_and_setattr(cls: type[T], attributes: dict[str, Any]) -> T:
    obj = cls()
    for key, value in attributes.items():
        setattr(obj, key, value)
    return obj


def _init_kwargs(cls: type[T], attributes: Any) -> T:
    return cls(**attributes)


def _try_parsers(
    value_parsers: tuple[TParseFunc[Any], ...],
    source_value: Any,
    target_type: type[T],
) -> T | NoMatch | LazyMatch[T]:
    for parser in value_parsers:
        result = parser(source_value, target_type)
        if not isinstance(result, NoMatch):
            return result

    return NoMatch()


def _parse_value(
    value: Any,
    t_key: type[T],
    value_parsers: tuple[TParseFunc[Any], ...],
) -> T | None:
    result = _try_parsers(value_parsers, value, t_key)
    if isinstance(result, NoMatch):
        return None
    if isinstance(result, LazyMatch):
        parser = get_parser_with_no_defaults(*value_parsers)
        return result.resolve_with(parser)
    return result


def _parse_key(
    data: dict[Any, Any],
    key: str,
    t_key: type,
    value_parsers: tuple[TParseFunc[Any], ...],
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
    value_parsers: tuple[TParseFunc[Any], ...],
    data: dict[str, Any],
) -> dict[str, Any]:
    return {
        key: _parse_key(data, key, t_key, value_parsers)
        for key, t_key in annotations.items()
    }


def _parse_flat(
    target_type: type[T],
    value_parsers: tuple[TParseFunc[Any], ...],
    data: Any,
    optional: bool,
) -> T | None:
    parsed = _parse_value(data, target_type, value_parsers)

    if optional and parsed is None:
        return None

    target_origin: type[T] = get_origin(target_type) or target_type
    if isinstance(parsed, target_origin):
        return parsed

    raise TypeError()


def _get_optional_or_orig(target_type: type) -> tuple[type, bool]:
    if get_origin(target_type) is Union:
        (target_type,) = (
            t for t in get_args(target_type) if t is not NoneType
        )
        return target_type, True
    return target_type, False


def _parse(
    value_parsers: tuple[TParseFunc[Any], ...],
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


def get_parser_with_no_defaults(
    *value_parsers: TParseFunc[Any],
) -> Callable[[type[T]], Callable[[Any], T | None]]:
    """get parser func that uses the provided value parsers

    Parsers will be used in order until parsing succeeds.

    Raises:
        TypeError: When no parser matched
    """

    def partial_parse(target_type: type[T]) -> Callable[[Any], T | None]:
        def parse(value: Any) -> T | None:
            return _parse(value_parsers, target_type, value)

        return parse

    return partial_parse


def get_parser(
    *value_parsers: TParseFunc[Any],
) -> Callable[[type[T]], Callable[[Any], T | None]]:
    """
    get parser func which always attempts to use `DEFAULT_VALUE_PARSERS`
    after provided parsers did not match.

    Parsers will be used in order until parsing succeeds.

    Raises:
        TypeError: When no parser matched
    """
    return get_parser_with_no_defaults(
        *(value_parsers + DEFAULT_VALUE_PARSERS)
    )
