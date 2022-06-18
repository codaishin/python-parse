"""parse"""

from abc import abstractmethod
from dataclasses import is_dataclass
from functools import partial, reduce
from inspect import get_annotations
from types import NoneType
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Optional,
    TypeVar,
    get_args,
)

T = TypeVar("T")
TTarget = TypeVar("TTarget")
TSource = TypeVar("TSource")
TParseFunc = Callable[[Any], T]
TMatchRating = int

TYPE_ERROR_MSG = "'{key}' in data not compatible with '{type}'"
KEY_ERROR_MSG = "'{key}' not found in data"


class IParser(Generic[TTarget]):
    """parser interface"""

    @abstractmethod
    def match(
        self,
        source_type: type,
        target_type: type,
    ) -> TMatchRating:
        """checks, weather this parser is applicable

        Returns:
            TMatchRating:
                The higher the rating the better this parser matches
                the the provided types. `0` means the parser should not be
                used for parsing the provided types.
        """

    @abstractmethod
    def parse(self, value: Any) -> TTarget:
        """parse the provided value to the target type"""


class MatchSubtype(IParser[object]):
    """
    Applied to source values that are a subtype of the target
    value.

    If valid: has a match rating of 1
    """

    def match(self, source_type: type, target_type: type) -> TMatchRating:
        return 1 if issubclass(source_type, target_type) else 0

    def parse(self, value: object) -> object:
        return value


DEFAULT_VALUE_PARSERS = (MatchSubtype(),)


class _NullError(Exception):
    ...


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
    try:
        return value.__origin__
    except AttributeError:
        return value


def _is_iterable(t_key: Any, value: Any, *assert_types: Any) -> bool:
    if not _is_iterable_candidate(t_key, value):
        return False
    for assert_type in assert_types:
        if _origin(t_key) is _origin(assert_type):
            return True
    return False


def _is_optional(t_key: Any) -> bool:
    return _origin(t_key) is _origin(Optional[Any])


def _parse_required(
    value: Any,
    t_key: type,
    value_parsers: tuple[IParser[Any], ...],
) -> Any:
    if _is_iterable(t_key, value, list):
        (t_key,) = get_args(t_key)
        return [_parse_value(e, t_key, value_parsers) for e in value]
    if _is_iterable(t_key, value, tuple, Iterable):
        (t_key,) = get_args(t_key)
        return tuple((_parse_value(e, t_key, value_parsers) for e in value))
    if isinstance(value, dict):
        parse: TParseFunc[Any] = get_parser(*value_parsers)(t_key)
        return parse(value)
    if isinstance(value, (list, tuple)) and len(value) == 1:
        return _parse_value(value[0], t_key, value_parsers)
    if not value_parsers:
        raise TypeError()
    (parse, match) = _get_best_value_parser(value_parsers, type(value), t_key)
    if not match:
        raise TypeError()
    parsed_value = parse(value)
    if not isinstance(parsed_value, t_key):
        raise TypeError()
    return parsed_value


TParserData = tuple[IParser[Any], TMatchRating]


def _best_parser_for(
    source_type: type,
    target_type: type,
) -> Callable[[TParserData, IParser[Any]], TParserData,]:
    def run(aggr: TParserData, crnt: IParser[Any]) -> TParserData:
        crnt_match = crnt.match(source_type, target_type)
        (_, aggr_match) = aggr
        if crnt_match > aggr_match:
            return (crnt, crnt_match)
        return aggr

    return run


def _get_best_value_parser(
    value_parsers: tuple[IParser[Any], ...],
    source_type: type,
    target_type: type,
) -> tuple[TParseFunc[Any], TMatchRating]:
    (fst, *remaining) = value_parsers
    (parser, best_match) = reduce(
        _best_parser_for(source_type, target_type),
        remaining,
        (fst, fst.match(source_type, target_type)),
    )
    return parser.parse, best_match


def _parse_optional(
    value: Any,
    t_key: Any,
    sub_parsers: tuple[IParser[Any], ...],
) -> Any:
    if value is None:
        return None

    (t_key,) = (t for t in get_args(t_key) if t is not NoneType)
    return _parse_required(value, t_key, sub_parsers)


def _parse_value(
    value: Any,
    t_key: Any,
    sub_parsers: tuple[IParser[Any], ...],
) -> Any:
    if _is_optional(t_key):
        return _parse_optional(value, t_key, sub_parsers)
    if value is None:
        raise _NullError()
    return _parse_required(value, t_key, sub_parsers)


def _parse_key(
    data: dict[Any, Any],
    key: str,
    t_key: Any,
    sub_parsers: tuple[IParser[Any], ...],
) -> Any:
    try:
        return _parse_value(data.get(key, None), t_key, sub_parsers)
    except TypeError as err:
        raise TypeError(TYPE_ERROR_MSG.format(key=key, type=t_key)) from err
    except _NullError as err:
        raise KeyError(KEY_ERROR_MSG.format(key=key)) from err


def _get_attributes(
    t_data: type,
    sub_parsers: tuple[IParser[Any], ...],
    data: dict[str, Any],
) -> dict[str, Any]:
    annotations = get_annotations(t_data).items()
    return {
        key: _parse_key(data, key, t_key, sub_parsers)
        for key, t_key in annotations
    }


def _parse(
    value_parsers: tuple[IParser[Any], ...],
    target_type: type[T],
    data: dict[Any, Any],
) -> T:
    attributes = _get_attributes(target_type, value_parsers, data)
    if is_dataclass(target_type):
        return _init_kwargs(target_type, attributes)
    return _init_and_setattr(target_type, attributes)


def get_parser(
    *value_parsers: IParser[Any],
) -> Callable[[type[T]], TParseFunc[T]]:
    """get parser func that uses the provided value parsers"""

    def parse_partial(target_type: type[T]) -> TParseFunc[T]:
        return partial(_parse, value_parsers, target_type)

    return parse_partial


def get_parser_default(
    *value_parsers: IParser[Any],
) -> Callable[[type[T]], TParseFunc[T]]:
    """
    get parser func which always uses at least `DEFAULT_VALUE_PARSERS`
    """
    return get_parser(*(value_parsers + DEFAULT_VALUE_PARSERS))
