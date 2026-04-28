"""
.. module:: test_dbconnection
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for :mod:`automojo.storage.database.dbconnection`.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"

import unittest

from unittest import mock

from automojo.errors.exceptions import ConfigurationError
from automojo.storage.database import dbconnection
from automojo.storage.database.dbconnection import (
    BasicSocketDatabaseConnectionFactory,
    BasicTcpDatabaseConnectionFactory,
    DatabaseConnectionFactory,
    create_database_connection_factory,
)


def _make_socket_profile(*, identifier: str = "socket-profile",
                         dbtype: str = "postgresql",
                         dbname: str = "primary_db",
                         socket_path: str = "/var/run/postgresql",
                         credential_name: str = "basic-login") -> mock.MagicMock:
    """
        Build a stand-in :class:`DatabaseBasicSocketProfile` mock.

        :param identifier: Identifier exposed on the profile.
        :param dbtype: Value for ``dbtype``.
        :param dbname: Value for ``dbname``.
        :param socket_path: Value for ``socket``.
        :param credential_name: Value for ``credential``.

        :returns: Mock object exposing the same attributes the production
            profile exposes.
    """
    profile = mock.MagicMock()
    profile.identifier = identifier
    profile.category = "basic-socket"
    profile.dbtype = dbtype
    profile.dbname = dbname
    profile.socket = socket_path
    profile.credential = credential_name
    return profile


def _make_tcp_profile(*, identifier: str = "tcp-profile",
                      dbtype: str = "postgresql",
                      dbname: str = "primary_db",
                      host: str = "db.example.com",
                      port: int = 5432,
                      credential_name: str = "basic-login") -> mock.MagicMock:
    """
        Build a stand-in :class:`DatabaseBasicTcpProfile` mock.

        :param identifier: Identifier exposed on the profile.
        :param dbtype: Value for ``dbtype``.
        :param dbname: Value for ``dbname``.
        :param host: Value for ``host``.
        :param port: Value for ``port``.
        :param credential_name: Value for ``credential``.

        :returns: Mock object exposing the same attributes the production
            profile exposes.
    """
    profile = mock.MagicMock()
    profile.identifier = identifier
    profile.category = "basic-tcp"
    profile.dbtype = dbtype
    profile.dbname = dbname
    profile.host = host
    profile.port = port
    profile.credential = credential_name
    return profile


def _make_basic_credential(*, username: str = "ubuntu",
                           password: str = "secret") -> "mock.MagicMock":
    """
        Build a :class:`BasicCredential`-shaped mock that passes ``isinstance``
        checks against the real :class:`BasicCredential` class.

        :param username: Username exposed by the mock.
        :param password: Password exposed by the mock.

        :returns: Mock object of ``spec=BasicCredential``.
    """
    from automojo.credentials.basiccredential import BasicCredential

    cred = mock.MagicMock(spec=BasicCredential)
    cred.username = username
    cred.password = password
    return cred


def _make_non_basic_credential() -> "mock.MagicMock":
    """
        Build a credential mock that is not a :class:`BasicCredential` instance.

        :returns: Mock object of ``spec=BaseCredential``.
    """
    from automojo.credentials.basecredential import BaseCredential

    cred = mock.MagicMock(spec=BaseCredential)
    return cred


class TestDatabaseConnectionFactoryBase(unittest.TestCase):
    """
        Verify the behavior of the :class:`DatabaseConnectionFactory` base class.
    """

    def setUp(self) -> None:
        """
            Build a fresh profile and credential pair for each test.
        """
        self.profile = _make_socket_profile()
        self.credential = _make_basic_credential()
        return

    def test_constructor_stores_inputs(self) -> None:
        """
            Verify that constructor arguments are exposed via the corresponding
            properties.
        """
        factory = DatabaseConnectionFactory(
            "profile-x", dbprofile=self.profile, credential=self.credential)

        self.assertEqual(factory.profile_name, "profile-x")
        self.assertIs(factory.dbprofile, self.profile)
        self.assertIs(factory.credential, self.credential)
        return

    def test_create_engine_raises_not_implemented(self) -> None:
        """
            Verify that the base ``create_engine`` raises :class:`NotImplementedError`.
        """
        factory = DatabaseConnectionFactory(
            "profile-x", dbprofile=self.profile, credential=self.credential)

        with self.assertRaises(NotImplementedError):
            factory.create_engine()
        return


class TestBasicSocketDatabaseConnectionFactory(unittest.TestCase):
    """
        Verify the behavior of :class:`BasicSocketDatabaseConnectionFactory`.
    """

    def setUp(self) -> None:
        """
            Build a fresh socket profile and basic credential for each test.
        """
        self.profile = _make_socket_profile(
            socket_path="/var/run/postgresql",
            dbname="primary_db")
        self.credential = _make_basic_credential(
            username="ubuntu", password="secret")
        self.factory = BasicSocketDatabaseConnectionFactory(
            "socket-profile", dbprofile=self.profile, credential=self.credential)
        return

    def test_get_connection_scheme_postgresql(self) -> None:
        """
            Verify that postgresql profiles resolve to the
            ``postgresql+psycopg2`` SQLAlchemy scheme.
        """
        scheme = self.factory.get_connection_scheme()
        self.assertEqual(scheme, "postgresql+psycopg2")
        return

    def test_get_connection_scheme_unknown_returns_none(self) -> None:
        """
            Verify that unsupported dbtype values return ``None`` (the current
            behavior of the implementation).
        """
        unknown_profile = _make_socket_profile(dbtype="mysql")
        factory = BasicSocketDatabaseConnectionFactory(
            "socket-profile", dbprofile=unknown_profile, credential=self.credential)

        scheme = factory.get_connection_scheme()
        self.assertIsNone(scheme)
        return

    def test_format_connection_string_uses_profile_dbname(self) -> None:
        """
            Verify that the connection string falls back to the profile
            ``dbname`` when no override is supplied.
        """
        conn_str = self.factory.format_connection_string()
        expected = "postgresql+psycopg2://ubuntu:secret@/primary_db?host=/var/run/postgresql"
        self.assertEqual(conn_str, expected)
        return

    def test_format_connection_string_uses_override_dbname(self) -> None:
        """
            Verify that an explicit ``dbname`` override is honored.
        """
        conn_str = self.factory.format_connection_string(dbname="alternate_db")
        expected = "postgresql+psycopg2://ubuntu:secret@/alternate_db?host=/var/run/postgresql"
        self.assertEqual(conn_str, expected)
        return

    def test_format_connection_string_with_non_basic_credential_raises(self) -> None:
        """
            Verify that supplying a non-:class:`BasicCredential` raises
            :class:`ConfigurationError`.
        """
        bad_credential = _make_non_basic_credential()
        factory = BasicSocketDatabaseConnectionFactory(
            "socket-profile", dbprofile=self.profile, credential=bad_credential)

        with self.assertRaises(ConfigurationError):
            factory.format_connection_string()
        return

    def test_create_engine_invokes_sqlalchemy_create_engine(self) -> None:
        """
            Verify that ``create_engine`` builds the connection string and
            forwards it to ``sqlalchemy.create_engine`` with ``echo``.
        """
        sentinel_engine = mock.MagicMock(name="sentinel_engine")

        with mock.patch.object(dbconnection, "create_engine", return_value=sentinel_engine) as mock_ce:
            engine = self.factory.create_engine(dbname="alternate_db", echo=False)

        expected_conn = "postgresql+psycopg2://ubuntu:secret@/alternate_db?host=/var/run/postgresql"
        mock_ce.assert_called_once_with(expected_conn, echo=False)
        self.assertIs(engine, sentinel_engine)
        return

    def test_create_engine_with_non_basic_credential_raises(self) -> None:
        """
            Verify that ``create_engine`` raises when the credential is not a
            :class:`BasicCredential`.
        """
        bad_credential = _make_non_basic_credential()
        factory = BasicSocketDatabaseConnectionFactory(
            "socket-profile", dbprofile=self.profile, credential=bad_credential)

        with self.assertRaises(ConfigurationError):
            factory.create_engine()
        return

    def test_create_engine_falls_back_to_profile_dbname(self) -> None:
        """
            Verify that omitting ``dbname`` causes the factory to use the
            profile-supplied database name.
        """
        sentinel_engine = mock.MagicMock(name="sentinel_engine")

        with mock.patch.object(dbconnection, "create_engine", return_value=sentinel_engine) as mock_ce:
            self.factory.create_engine()

        called_args, called_kwargs = mock_ce.call_args
        self.assertIn("primary_db", called_args[0])
        self.assertEqual(called_kwargs.get("echo"), True)
        return


class TestBasicTcpDatabaseConnectionFactory(unittest.TestCase):
    """
        Verify the behavior of :class:`BasicTcpDatabaseConnectionFactory`.
    """

    def setUp(self) -> None:
        """
            Build a fresh TCP profile and basic credential for each test.
        """
        self.profile = _make_tcp_profile(
            host="db.example.com",
            port=5432,
            dbname="primary_db")
        self.credential = _make_basic_credential(
            username="ubuntu", password="secret")
        self.factory = BasicTcpDatabaseConnectionFactory(
            "tcp-profile", dbprofile=self.profile, credential=self.credential)
        return

    def test_get_connection_scheme_postgresql(self) -> None:
        """
            Verify that postgresql profiles resolve to the
            ``postgresql+psycopg2`` SQLAlchemy scheme.
        """
        scheme = self.factory.get_connection_scheme()
        self.assertEqual(scheme, "postgresql+psycopg2")
        return

    def test_get_connection_scheme_unknown_returns_none(self) -> None:
        """
            Verify that unsupported dbtype values return ``None``.
        """
        unknown_profile = _make_tcp_profile(dbtype="mysql")
        factory = BasicTcpDatabaseConnectionFactory(
            "tcp-profile", dbprofile=unknown_profile, credential=self.credential)

        scheme = factory.get_connection_scheme()
        self.assertIsNone(scheme)
        return

    def test_format_connection_string_with_override_dbname(self) -> None:
        """
            Verify TCP connection-string formatting honors a ``dbname`` override.
        """
        conn_str = self.factory.format_connection_string(dbname="alternate_db")
        expected = "postgresql+psycopg2://ubuntu:secret@db.example.com:5432/alternate_db"
        self.assertEqual(conn_str, expected)
        return

    def test_format_connection_string_default_dbname_uses_profile(self) -> None:
        """
            Verify TCP connection-string formatting falls back to the profile
            ``dbname`` when no override is supplied.
        """
        conn_str = self.factory.format_connection_string()
        expected = "postgresql+psycopg2://ubuntu:secret@db.example.com:5432/primary_db"
        self.assertEqual(conn_str, expected)
        return

    def test_format_connection_string_with_non_basic_credential_returns_none(self) -> None:
        """
            Verify the TCP factory returns ``None`` (per current implementation)
            when the credential is not a :class:`BasicCredential`.
        """
        bad_credential = _make_non_basic_credential()
        factory = BasicTcpDatabaseConnectionFactory(
            "tcp-profile", dbprofile=self.profile, credential=bad_credential)

        conn_str = factory.format_connection_string()
        self.assertIsNone(conn_str)
        return

    def test_create_engine_invokes_sqlalchemy_create_engine(self) -> None:
        """
            Verify that the TCP factory ``create_engine`` builds the connection
            string and forwards it to ``sqlalchemy.create_engine``.
        """
        sentinel_engine = mock.MagicMock(name="sentinel_engine")

        with mock.patch.object(dbconnection, "create_engine", return_value=sentinel_engine) as mock_ce:
            engine = self.factory.create_engine(dbname="alternate_db", echo=False)

        expected_conn = "postgresql+psycopg2://ubuntu:secret@db.example.com:5432/alternate_db"
        mock_ce.assert_called_once_with(expected_conn, echo=False)
        self.assertIs(engine, sentinel_engine)
        return


class TestCreateDatabaseConnectionFactory(unittest.TestCase):
    """
        Verify the behavior of :func:`create_database_connection_factory`.
    """

    def setUp(self) -> None:
        """
            Snapshot and clear the module-level factory cache before each test
            so that tests do not share cached state.
        """
        self.previous_cache = dict(dbconnection.DATABASE_CONNECTION_FACTORIES)
        dbconnection.DATABASE_CONNECTION_FACTORIES.clear()
        return

    def tearDown(self) -> None:
        """
            Restore the previously snapshot factory cache.
        """
        dbconnection.DATABASE_CONNECTION_FACTORIES.clear()
        dbconnection.DATABASE_CONNECTION_FACTORIES.update(self.previous_cache)
        return

    def _make_credential_manager(self, *, credential_name: str,
                                 credential: "mock.MagicMock") -> "mock.MagicMock":
        """
            Build a credential-manager mock whose ``credentials`` mapping yields
            the supplied credential under the supplied key.

            :param credential_name: Key used to look up the credential.
            :param credential: Credential mock to return for ``credential_name``.

            :returns: A mock with a ``credentials`` dict-like attribute.
        """
        cred_manager = mock.MagicMock()
        cred_manager.credentials = {credential_name: credential}
        return cred_manager

    def test_socket_profile_creates_socket_factory(self) -> None:
        """
            Verify that a ``basic-socket`` category profile yields a
            :class:`BasicSocketDatabaseConnectionFactory`.
        """
        profile = _make_socket_profile(identifier="socket-1")
        credential = _make_basic_credential()
        cred_manager = self._make_credential_manager(
            credential_name=profile.credential, credential=credential)

        factory = create_database_connection_factory(profile, cred_manager)

        self.assertIsInstance(factory, BasicSocketDatabaseConnectionFactory)
        self.assertEqual(factory.profile_name, "socket-1")
        return

    def test_tcp_profile_creates_tcp_factory(self) -> None:
        """
            Verify that a ``basic-tcp`` category profile yields a
            :class:`BasicTcpDatabaseConnectionFactory`.
        """
        profile = _make_tcp_profile(identifier="tcp-1")
        credential = _make_basic_credential()
        cred_manager = self._make_credential_manager(
            credential_name=profile.credential, credential=credential)

        factory = create_database_connection_factory(profile, cred_manager)

        self.assertIsInstance(factory, BasicTcpDatabaseConnectionFactory)
        self.assertEqual(factory.profile_name, "tcp-1")
        return

    def test_unknown_category_raises_configuration_error(self) -> None:
        """
            Verify that an unsupported profile category raises
            :class:`ConfigurationError`.
        """
        profile = _make_socket_profile(identifier="weird-1")
        profile.category = "weird-category"
        credential = _make_basic_credential()
        cred_manager = self._make_credential_manager(
            credential_name=profile.credential, credential=credential)

        with self.assertRaises(ConfigurationError):
            create_database_connection_factory(profile, cred_manager)
        return

    def test_factory_is_cached_by_profile_identifier(self) -> None:
        """
            Verify that repeated calls with the same profile identifier return
            the same cached factory instance.
        """
        profile = _make_socket_profile(identifier="cached-1")
        credential = _make_basic_credential()
        cred_manager = self._make_credential_manager(
            credential_name=profile.credential, credential=credential)

        first = create_database_connection_factory(profile, cred_manager)
        second = create_database_connection_factory(profile, cred_manager)

        self.assertIs(first, second)
        return


if __name__ == "__main__":
    unittest.main()
