"""
.. module:: test_mixins
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for :mod:`ccai.storage.database.mixins`.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"

import json
import unittest

from types import SimpleNamespace
from unittest import mock

from ccai.storage.database import mixins
from ccai.storage.database.mixins import SerializableMixIn


class _FakeModel(SerializableMixIn):
    """
        Minimal stand-in model used as the subject under test for the
        :class:`SerializableMixIn` mixin. Holds a small set of attributes
        whose names are advertised through a mocked ``inspect`` mapper.
    """

    def __init__(self, *, identifier: int, name: str) -> None:
        """
            Store the attributes that the mixin will iterate during serialization.

            :param identifier: Numeric identifier exposed as ``id``.
            :param name: Display name attribute.
        """
        self.id = identifier
        self.name = name
        return


def _make_fake_mapper(attribute_keys: list) -> mock.MagicMock:
    """
        Build a mock SQLAlchemy mapper with an ``attrs`` collection of fake columns.

        :param attribute_keys: Names of attributes the mapper should advertise.

        :returns: Mock object whose ``attrs`` mirrors the supplied keys.
    """
    fake_attrs = []
    for key in attribute_keys:
        fake_col = SimpleNamespace(key=key)
        fake_attrs.append(fake_col)

    mapper = mock.MagicMock()
    mapper.attrs = fake_attrs

    return mapper


class TestSerializableMixInAsDict(unittest.TestCase):
    """
        Verify the behavior of :meth:`SerializableMixIn.as_dict`.
    """

    def setUp(self) -> None:
        """
            Build a fresh :class:`_FakeModel` instance for each test.
        """
        self.subject = _FakeModel(identifier=42, name="alpha")
        return

    def test_returns_dict_with_string_values(self) -> None:
        """
            Verify that ``as_dict`` returns a dict where every value is the
            ``str`` representation of the corresponding attribute.
        """
        mapper = _make_fake_mapper(attribute_keys=["id", "name"])
        recorded = {}

        def _fake_inspect(model_cls: type) -> object:
            recorded["model_cls"] = model_cls
            return mapper

        with mock.patch.object(mixins, "inspect", new=_fake_inspect):
            result = self.subject.as_dict()

        self.assertIs(recorded["model_cls"], _FakeModel)
        expected = {"id": "42", "name": "alpha"}
        self.assertEqual(result, expected)
        return

    def test_iterates_only_columns_supplied_by_mapper(self) -> None:
        """
            Verify that ``as_dict`` only includes attributes the mapper exposes.
        """
        # Only expose 'name' even though the model also has 'id'.
        mapper = _make_fake_mapper(attribute_keys=["name"])

        def _fake_inspect(model_cls: type) -> object:
            return mapper

        with mock.patch.object(mixins, "inspect", new=_fake_inspect):
            result = self.subject.as_dict()

        self.assertNotIn("id", result)
        self.assertIn("name", result)
        return

    def test_empty_mapper_returns_empty_dict(self) -> None:
        """
            Verify that a mapper with no attributes yields an empty dict.
        """
        mapper = _make_fake_mapper(attribute_keys=[])

        def _fake_inspect(model_cls: type) -> object:
            return mapper

        with mock.patch.object(mixins, "inspect", new=_fake_inspect):
            result = self.subject.as_dict()

        self.assertEqual(result, {})
        return

    def test_handles_none_attribute_value(self) -> None:
        """
            Verify that ``None`` values are stringified as ``"None"``.
        """
        self.subject.name = None
        mapper = _make_fake_mapper(attribute_keys=["name"])

        def _fake_inspect(model_cls: type) -> object:
            return mapper

        with mock.patch.object(mixins, "inspect", new=_fake_inspect):
            result = self.subject.as_dict()

        self.assertEqual(result, {"name": "None"})
        return


class TestSerializableMixInToJson(unittest.TestCase):
    """
        Verify the behavior of :meth:`SerializableMixIn.to_json`.
    """

    def setUp(self) -> None:
        """
            Build a fresh :class:`_FakeModel` instance for each test.
        """
        self.subject = _FakeModel(identifier=7, name="beta")
        return

    def test_returns_json_string_with_default_indent(self) -> None:
        """
            Verify that ``to_json`` returns a JSON-formatted string with default
            indentation that round-trips back to the dictionary form.
        """
        mapper = _make_fake_mapper(attribute_keys=["id", "name"])

        def _fake_inspect(model_cls: type) -> object:
            return mapper

        with mock.patch.object(mixins, "inspect", new=_fake_inspect):
            json_str = self.subject.to_json()

        self.assertIsInstance(json_str, str)
        decoded = json.loads(json_str)
        expected = {"id": "7", "name": "beta"}
        self.assertEqual(decoded, expected)
        return

    def test_default_indent_is_four_spaces(self) -> None:
        """
            Verify that the default JSON output uses an indent of four spaces.
        """
        mapper = _make_fake_mapper(attribute_keys=["id"])

        def _fake_inspect(model_cls: type) -> object:
            return mapper

        with mock.patch.object(mixins, "inspect", new=_fake_inspect):
            json_str = self.subject.to_json()

        # With indent=4 the string should contain a newline followed by four
        # spaces before each key.
        self.assertIn("\n    ", json_str)
        return

    def test_custom_indent_is_honored(self) -> None:
        """
            Verify that a custom ``indent`` value is forwarded to ``json.dumps``.
        """
        mapper = _make_fake_mapper(attribute_keys=["id"])

        def _fake_inspect(model_cls: type) -> object:
            return mapper

        with mock.patch.object(mixins, "inspect", new=_fake_inspect):
            json_str = self.subject.to_json(indent=2)

        self.assertIn("\n  ", json_str)
        return

    def test_empty_model_serializes_to_empty_object(self) -> None:
        """
            Verify that a model with no advertised columns serializes to ``{}``.
        """
        mapper = _make_fake_mapper(attribute_keys=[])

        def _fake_inspect(model_cls: type) -> object:
            return mapper

        with mock.patch.object(mixins, "inspect", new=_fake_inspect):
            json_str = self.subject.to_json()

        decoded = json.loads(json_str)
        self.assertEqual(decoded, {})
        return


if __name__ == "__main__":
    unittest.main()
