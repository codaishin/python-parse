"""test tools"""

from functools import wraps
from typing import Callable, Type, TypeVar
from unittest import TestCase

TTestCase = TypeVar("TTestCase", bound="UnitTests")


def _wrap_name_and_docstring(
    func: Callable[[TTestCase], None],
    name: str,
    doc: str,
) -> Callable[[TTestCase], None]:
    wrapped = wraps(func)(func)
    wrapped.__doc__ = doc
    wrapped.__name__ = name
    return wrapped


def _add_func_to_class(
    cls: Type[TTestCase],
    name: str,
    func: Callable[[TTestCase], None],
) -> None:
    setattr(cls, name, func)


class UnitTests(TestCase):
    """Test collection to run tests on.
    Extends `TestCase` with a `describe` decorator,
    which allows adding of unnamed test methods to the class.
    Example:
    ```python
    class SumTests(UnitTests):
        \"\"\"sum() tests\"\"\"

    @SumTests.describe("1 + 1 == 2")
    def _(test: SumTests) -> None:
        test.assertEqual(2, sum(1, 1))
    ```
    """

    _func_names: list[str] = []

    @classmethod
    def describe(
        cls: Type[TTestCase],
        docstring: str,
    ) -> Callable[[Callable[[TTestCase], None]], Callable[[TTestCase], None]]:
        """add test with docstring"""

        def decorator(
            func: Callable[[TTestCase], None]
        ) -> Callable[[TTestCase], None]:
            func_name = "_".join(docstring.split(" "))
            cls._func_names.append(func_name)
            name = f"test_{func_name}"
            count = cls._func_names.count(func_name)
            if count > 1:
                name += f"_{count}"
            wrapped = _wrap_name_and_docstring(func, name, docstring)
            _add_func_to_class(cls, name, wrapped)
            return func

        return decorator
