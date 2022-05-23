"""test parse"""
from dataclasses import dataclass
from datetime import date
from typing import Generic, Iterable, Optional, TypeVar
from unittest import TestCase
from parse import Parse

T = TypeVar("T")


class TestParse(TestCase):
    """test parse"""

    def test_parse_model(self) -> None:
        """parse model"""

        # pylint: disable=too-few-public-methods
        class _Person:
            name: str
            age: int

        to_person = Parse(_Person)
        person = to_person({"name": "Harry", "age": 42})
        self.assertEqual((person.name, person.age), ("Harry", 42))

    def test_parse_single_list_vale(self) -> None:
        """parse model"""

        # pylint: disable=too-few-public-methods
        class _Person:
            name: str
            age: int

        to_person = Parse(_Person)
        person = to_person({"name": ["Harry"], "age": [42]})
        self.assertEqual((person.name, person.age), ("Harry", 42))

    def test_parse_single_optional_value(self) -> None:
        """parse model"""

        # pylint: disable=too-few-public-methods
        class _Person:
            name: Optional[str]
            age: Optional[int]
            birthday: Optional[date]

        to_person = Parse(_Person)
        person = to_person({"age": None, "birthday": date(2000, 1, 1)})
        self.assertEqual(
            (person.name, person.age, person.birthday),
            (None, None, date(2000, 1, 1)),
        )

    def test_parse_list_with_optional_values(self) -> None:
        """parse model"""

        # pylint: disable=too-few-public-methods
        class _Person:
            names: list[Optional[str]]

        to_person = Parse(_Person)
        person = to_person({"names": ["Rudy", None]})
        self.assertListEqual(person.names, ["Rudy", None])

    def test_parse_key_missing(self) -> None:
        """parse model"""

        # pylint: disable=too-few-public-methods
        class _Person:
            name: str
            age: int

        to_person = Parse(_Person)
        with self.assertRaises(KeyError) as ctx:
            _ = to_person({"age": 33})

        msg = Parse.KEY_ERROR.format(key="name")
        error = KeyError(msg)
        self.assertEqual(str(error), str(ctx.exception))

    def test_type_mismatch(self) -> None:
        """parse model"""

        # pylint: disable=too-few-public-methods
        class _Car:
            max_speed: int
            seats: int

        to_car = Parse(_Car)
        with self.assertRaises(TypeError) as ctx:
            _ = to_car({"max_speed": "foo", "seats": "bar"})

        msg = Parse.TYPE_ERROR.format(key="max_speed", type=int)
        error = TypeError(msg)
        self.assertEqual(str(error), str(ctx.exception))

    def test_type_mismatch_generic(self) -> None:
        """parse model"""

        # pylint: disable=too-few-public-methods
        class _Generic(Generic[T]):
            pass

        # pylint: disable=too-few-public-methods
        class _Mock:
            field: _Generic[int]

        to_mock = Parse(_Mock)
        with self.assertRaises(TypeError) as ctx:
            _ = to_mock({"field": 32})

        msg = Parse.TYPE_ERROR.format(key="field", type=_Generic[int])
        error = TypeError(msg)
        self.assertEqual(str(error), str(ctx.exception))

    def test_parse_nested(self) -> None:
        """parse model"""

        # pylint: disable=too-few-public-methods
        class _Address:
            street: str
            number: int

        # pylint: disable=too-few-public-methods
        class _Person:
            address: _Address
            name: str
            age: int

        to_person = Parse(_Person)
        person = to_person(
            {
                "name": "Jenny",
                "age": 22,
                "address": {
                    "street": "Sesame Street",
                    "number": 42,
                },
            }
        )
        self.assertEqual(
            (
                person.name,
                person.age,
                person.address.street,
                person.address.number,
            ),
            ("Jenny", 22, "Sesame Street", 42),
        )

    def test_parse_optional_nested(self) -> None:
        """parse model"""

        # pylint: disable=too-few-public-methods
        class _Address:
            street: str

        # pylint: disable=too-few-public-methods
        class _Person:
            fst_address: Optional[_Address]
            snd_address: Optional[_Address]
            trd_address: Optional[_Address]

        to_person = Parse(_Person)
        person = to_person(
            {
                "fst_address": {"street": "Sesame Street"},
                "snd_address": None,
            }
        )

        assert person.fst_address
        self.assertEqual(
            (
                person.fst_address.street,
                person.snd_address,
                person.trd_address,
            ),
            ("Sesame Street", None, None),
        )

    def test_parse_dataclass(self) -> None:
        """parse model"""

        @dataclass
        class _Person:
            name: str
            age: int

        to_person = Parse(_Person)
        person = to_person({"name": "Harry", "age": 42})
        self.assertEqual((person.name, person.age), ("Harry", 42))

    def test_parse_only_annotations(self) -> None:
        """parse model"""

        # pylint: disable=too-few-public-methods
        class _Person:
            name: str
            age: int
            species = "Human"

        to_person = Parse(_Person)
        person = to_person({"name": "Harry", "age": 42, "species": "Martian"})
        self.assertEqual(
            (person.name, person.age, person.species),
            ("Harry", 42, "Human"),
        )

    def test_list_field(self) -> None:
        """parse model"""

        # pylint: disable=too-few-public-methods
        class _Path:
            nodes: list[str]

        to_path = Parse(_Path)
        path = to_path({"nodes": ["path", "to", "target"]})
        self.assertIsInstance(path.nodes, list)
        self.assertListEqual(
            path.nodes,
            ["path", "to", "target"],
        )

    def test_tuple_field(self) -> None:
        """parse model"""

        # pylint: disable=too-few-public-methods
        class _Path:
            nodes: tuple[str]

        to_path = Parse(_Path)
        path = to_path({"nodes": ["path", "to", "target"]})
        self.assertIsInstance(path.nodes, tuple)
        self.assertListEqual(
            list(path.nodes),
            ["path", "to", "target"],
        )

    def test_iterable_field(self) -> None:
        """parse model"""

        # pylint: disable=too-few-public-methods
        class _Path:
            nodes: Iterable[str]

        to_path = Parse(_Path)
        path = to_path({"nodes": ["path", "to", "target"]})
        self.assertIsInstance(path.nodes, tuple)
        self.assertListEqual(
            list(path.nodes),
            ["path", "to", "target"],
        )
