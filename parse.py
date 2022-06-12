"""parse"""

from dataclasses import is_dataclass
from types import NoneType
from typing import Any, Generic, Iterable, Optional, Type, TypeVar, get_args

T = TypeVar("T")


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


def _parse_required(value: Any, t_key: Any) -> Any:
    if _is_iterable(t_key, value, list):
        (t_key,) = get_args(t_key)
        return [_parse_value(elem, t_key) for elem in value]
    if _is_iterable(t_key, value, tuple, Iterable):
        (t_key,) = get_args(t_key)
        return tuple((_parse_value(elem, t_key) for elem in value))
    if isinstance(value, dict):
        parse = Parse(t_key)
        return parse(value)
    if isinstance(value, t_key):
        return value
    if isinstance(value, (list, tuple)) and len(value) == 1:
        return _parse_value(value[0], t_key)
    raise TypeError()


def _parse_optional(value: Any, t_key: Any) -> Any:
    if value is None:
        return None

    (t_key,) = (t for t in get_args(t_key) if t is not NoneType)
    return _parse_required(value, t_key)


def _parse_value(value: Any, t_key: Any) -> Any:
    if _is_optional(t_key):
        return _parse_optional(value, t_key)
    if value is None:
        raise _NullError()
    return _parse_required(value, t_key)


def _parse_key(data: dict[Any, Any], key: str, t_key: Any) -> Any:
    try:
        return _parse_value(data.get(key, None), t_key)
    except TypeError as err:
        raise TypeError(Parse.TYPE_ERROR.format(key=key, type=t_key)) from err
    except _NullError as err:
        raise KeyError(Parse.KEY_ERROR.format(key=key)) from err


def _get_attributes(t_data: type, data: dict[str, Any]) -> dict[str, Any]:
    items = t_data.__annotations__.items()
    return {key: _parse_key(data, key, t_key) for key, t_key in items}


class _NullError(Exception):
    ...


# pylint: disable=too-few-public-methods
class Parse(Generic[T]):
    """Parse"""

    TYPE_ERROR = "'{key}' in data not compatible with '{type}'"
    KEY_ERROR = "'{key}' not found in data"

    def __init__(self, target_type: Type[T]) -> None:
        self._target_type = target_type

    def __call__(self, data: dict[Any, Any]) -> T:
        attributes = _get_attributes(self._target_type, data)

        if is_dataclass(self._target_type):
            return _init_kwargs(self._target_type, attributes)
        return _init_and_setattr(self._target_type, attributes)
