"""parse"""

from abc import abstractmethod
from dataclasses import is_dataclass
from functools import reduce
from types import NoneType
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Optional,
    Type,
    TypeVar,
    get_args,
)

T = TypeVar("T")
TTarget = TypeVar("TTarget")
TSource = TypeVar("TSource")
TMatchRating = int


class SubParser(Generic[TSource, TTarget]):
    """parser interface"""

    def __init__(
        self,
        source_type: Type[TSource],
        target_type: Type[TTarget],
    ) -> None:
        self._source_type = source_type
        self._target_type = target_type

    @property
    def source_type(self) -> Type[TSource]:
        """source type"""
        return self._source_type

    @property
    def target_type(self) -> Type[TTarget]:
        """target type"""
        return self._target_type

    @abstractmethod
    def match(
        self,
        source_type: type[TSource],
        target_type: type[TTarget],
    ) -> TMatchRating:
        """checks, weather this parser is applicable for the current key"""

    @abstractmethod
    def parse(self, value: TSource) -> TTarget:
        """execute the paring"""


class _TypeError(SubParser[Any, Any]):
    def __init__(self) -> None:
        super().__init__(object, object)

    def match(
        self,
        source_type: type[TSource],
        target_type: type[TTarget],
    ) -> TMatchRating:
        return 0

    def parse(self, value: TSource) -> TTarget:
        raise TypeError()


def _init_and_setattr(cls: Type[T], attributes: dict[str, Any]) -> T:
    obj = cls()
    for key, value in attributes.items():
        setattr(obj, key, value)
    return obj


def _init_kwargs(cls: Type[T], attributes: Any) -> T:
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
    t_key: Any,
    sub_parsers: tuple[SubParser[Any, Any], ...],
) -> Any:
    if _is_iterable(t_key, value, list):
        (t_key,) = get_args(t_key)
        return [_parse_value(e, t_key, sub_parsers) for e in value]
    if _is_iterable(t_key, value, tuple, Iterable):
        (t_key,) = get_args(t_key)
        return tuple((_parse_value(e, t_key, sub_parsers) for e in value))
    if isinstance(value, dict):
        parse = Parse(t_key, sub_parsers)
        return parse(value)
    if isinstance(value, t_key):
        return value
    if isinstance(value, (list, tuple)) and len(value) == 1:
        return _parse_value(value[0], t_key, sub_parsers)
    value_parser = _get_best_sub_parser(sub_parsers, type(value), t_key)
    return value_parser.parse(value)


TSubParseData = tuple[SubParser[Any, Any], TMatchRating]


def _get_match(
    sub_parser: SubParser[Any, Any],
    source_type: type,
    target_type: type,
) -> TMatchRating:
    if not issubclass(source_type, sub_parser.source_type):
        return 0
    if not issubclass(target_type, sub_parser.target_type):
        return 0
    return sub_parser.match(source_type, target_type)


def _best_parser_for(
    source_type: type,
    target_type: type,
) -> Callable[[TSubParseData, SubParser[Any, Any]], TSubParseData,]:
    def run(aggr: TSubParseData, crnt: SubParser[Any, Any]) -> TSubParseData:
        crnt_match = _get_match(crnt, source_type, target_type)
        (_, aggr_match) = aggr
        if crnt_match > aggr_match:
            return (crnt, crnt_match)
        return aggr

    return run


def _get_best_sub_parser(
    sub_parsers: tuple[SubParser[Any, Any], ...],
    source_type: type,
    target_type: type,
) -> SubParser[Any, Any]:
    type_error: SubParser[Any, Any] = _TypeError()
    (parser, _) = reduce(
        _best_parser_for(source_type, target_type),
        sub_parsers,
        (type_error, 0),
    )
    return parser


def _parse_optional(
    value: Any,
    t_key: Any,
    sub_parsers: tuple[SubParser[Any, Any], ...],
) -> Any:
    if value is None:
        return None

    (t_key,) = (t for t in get_args(t_key) if t is not NoneType)
    return _parse_required(value, t_key, sub_parsers)


def _parse_value(
    value: Any,
    t_key: Any,
    sub_parsers: tuple[SubParser[Any, Any], ...],
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
    sub_parsers: tuple[SubParser[Any, Any], ...],
) -> Any:
    try:
        return _parse_value(data.get(key, None), t_key, sub_parsers)
    except TypeError as err:
        raise TypeError(Parse.TYPE_ERROR.format(key=key, type=t_key)) from err
    except _NullError as err:
        raise KeyError(Parse.KEY_ERROR.format(key=key)) from err


def _get_attributes(
    t_data: type,
    sub_parsers: tuple[SubParser[Any, Any], ...],
    data: dict[str, Any],
) -> dict[str, Any]:
    items = t_data.__annotations__.items()
    return {
        key: _parse_key(data, key, t_key, sub_parsers) for key, t_key in items
    }


class _NullError(Exception):
    ...


# pylint: disable=too-few-public-methods
class Parse(Generic[T]):
    """Parse"""

    TYPE_ERROR = "'{key}' in data not compatible with '{type}'"
    KEY_ERROR = "'{key}' not found in data"

    def __init__(
        self,
        target_type: Type[T],
        sub_parsers: tuple[SubParser[Any, Any], ...] = (),
    ) -> None:
        self._target_type = target_type
        self._sub_parsers = sub_parsers

    def __call__(self, data: dict[Any, Any]) -> T:
        attributes = _get_attributes(
            self._target_type,
            self._sub_parsers,
            data,
        )

        if is_dataclass(self._target_type):
            return _init_kwargs(self._target_type, attributes)
        return _init_and_setattr(self._target_type, attributes)
