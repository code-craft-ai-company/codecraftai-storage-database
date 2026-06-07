"""
.. module:: test_mixins
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for :mod:`automojo.storage.database.mixins`.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"

import json

from types import SimpleNamespace
from unittest import mock

from automojo.storage.database import mixins
from automojo.storage.database.mixins import SerializableMixIn


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


def _establish_subject(identifier: int, name: str) -> _FakeModel:
    """
        Build a fresh :class:`_FakeModel` instance for a test. This replicates
        the per-test ``setUp`` of the original unittest test classes.

        :param identifier: Numeric identifier exposed as ``id``.
        :param name: Display name attribute.

        :returns: A freshly constructed :class:`_FakeModel`.
    """
    subject = _FakeModel(identifier=identifier, name=name)
    return subject


def test_returns_dict_with_string_values() -> None:
    """
        Verify that ``as_dict`` returns a dict where every value is the
        ``str`` representation of the corresponding attribute.
    """
    subject = _establish_subject(identifier=42, name="alpha")

    mapper = _make_fake_mapper(attribute_keys=["id", "name"])
    recorded = {}

    def _fake_inspect(model_cls: type) -> object:
        recorded["model_cls"] = model_cls
        return mapper

    with mock.patch.object(mixins, "inspect", new=_fake_inspect):
        result = subject.as_dict()

    assert recorded["model_cls"] is _FakeModel
    expected = {"id": "42", "name": "alpha"}
    assert result == expected
    return


def test_iterates_only_columns_supplied_by_mapper() -> None:
    """
        Verify that ``as_dict`` only includes attributes the mapper exposes.
    """
    subject = _establish_subject(identifier=42, name="alpha")

    # Only expose 'name' even though the model also has 'id'.
    mapper = _make_fake_mapper(attribute_keys=["name"])

    def _fake_inspect(model_cls: type) -> object:
        return mapper

    with mock.patch.object(mixins, "inspect", new=_fake_inspect):
        result = subject.as_dict()

    assert "id" not in result
    assert "name" in result
    return


def test_empty_mapper_returns_empty_dict() -> None:
    """
        Verify that a mapper with no attributes yields an empty dict.
    """
    subject = _establish_subject(identifier=42, name="alpha")

    mapper = _make_fake_mapper(attribute_keys=[])

    def _fake_inspect(model_cls: type) -> object:
        return mapper

    with mock.patch.object(mixins, "inspect", new=_fake_inspect):
        result = subject.as_dict()

    assert result == {}
    return


def test_handles_none_attribute_value() -> None:
    """
        Verify that ``None`` values are stringified as ``"None"``.
    """
    subject = _establish_subject(identifier=42, name="alpha")

    subject.name = None
    mapper = _make_fake_mapper(attribute_keys=["name"])

    def _fake_inspect(model_cls: type) -> object:
        return mapper

    with mock.patch.object(mixins, "inspect", new=_fake_inspect):
        result = subject.as_dict()

    assert result == {"name": "None"}
    return


def test_returns_json_string_with_default_indent() -> None:
    """
        Verify that ``to_json`` returns a JSON-formatted string with default
        indentation that round-trips back to the dictionary form.
    """
    subject = _establish_subject(identifier=7, name="beta")

    mapper = _make_fake_mapper(attribute_keys=["id", "name"])

    def _fake_inspect(model_cls: type) -> object:
        return mapper

    with mock.patch.object(mixins, "inspect", new=_fake_inspect):
        json_str = subject.to_json()

    assert isinstance(json_str, str)
    decoded = json.loads(json_str)
    expected = {"id": "7", "name": "beta"}
    assert decoded == expected
    return


def test_default_indent_is_four_spaces() -> None:
    """
        Verify that the default JSON output uses an indent of four spaces.
    """
    subject = _establish_subject(identifier=7, name="beta")

    mapper = _make_fake_mapper(attribute_keys=["id"])

    def _fake_inspect(model_cls: type) -> object:
        return mapper

    with mock.patch.object(mixins, "inspect", new=_fake_inspect):
        json_str = subject.to_json()

    # With indent=4 the string should contain a newline followed by four
    # spaces before each key.
    assert "\n    " in json_str
    return


def test_custom_indent_is_honored() -> None:
    """
        Verify that a custom ``indent`` value is forwarded to ``json.dumps``.
    """
    subject = _establish_subject(identifier=7, name="beta")

    mapper = _make_fake_mapper(attribute_keys=["id"])

    def _fake_inspect(model_cls: type) -> object:
        return mapper

    with mock.patch.object(mixins, "inspect", new=_fake_inspect):
        json_str = subject.to_json(indent=2)

    assert "\n  " in json_str
    return


def test_empty_model_serializes_to_empty_object() -> None:
    """
        Verify that a model with no advertised columns serializes to ``{}``.
    """
    subject = _establish_subject(identifier=7, name="beta")

    mapper = _make_fake_mapper(attribute_keys=[])

    def _fake_inspect(model_cls: type) -> object:
        return mapper

    with mock.patch.object(mixins, "inspect", new=_fake_inspect):
        json_str = subject.to_json()

    decoded = json.loads(json_str)
    assert decoded == {}
    return
