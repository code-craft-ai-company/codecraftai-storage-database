"""
.. module:: test_dbconnection
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Testbase tests for :mod:`ccai.storage.database.dbconnection`.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"

from typing import Dict, Tuple

from unittest import mock

from ccai.errors.exceptions import ConfigurationError
from ccai.storage.database import dbconnection
from ccai.storage.database.dbconnection import (
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
    from ccai.credentials.basiccredential import BasicCredential

    cred = mock.MagicMock(spec=BasicCredential)
    cred.username = username
    cred.password = password
    return cred


def _make_non_basic_credential() -> "mock.MagicMock":
    """
        Build a credential mock that is not a :class:`BasicCredential` instance.

        :returns: Mock object of ``spec=BaseCredential``.
    """
    from ccai.credentials.basecredential import BaseCredential

    cred = mock.MagicMock(spec=BaseCredential)
    return cred


def _make_credential_manager(*, credential_name: str,
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


def _establish_base_env() -> Tuple["mock.MagicMock", "mock.MagicMock"]:
    """
        Replicates the original ``TestDatabaseConnectionFactoryBase.setUp`` by
        building a fresh profile and credential pair.

        :returns: A ``(profile, credential)`` tuple.
    """
    profile = _make_socket_profile()
    credential = _make_basic_credential()
    rtnval = (profile, credential)
    return rtnval


def _establish_socket_env() -> Tuple["mock.MagicMock", "mock.MagicMock",
                                      BasicSocketDatabaseConnectionFactory]:
    """
        Replicates the original
        ``TestBasicSocketDatabaseConnectionFactory.setUp`` by building a fresh
        socket profile, basic credential, and factory.

        :returns: A ``(profile, credential, factory)`` tuple.
    """
    profile = _make_socket_profile(
        socket_path="/var/run/postgresql",
        dbname="primary_db")
    credential = _make_basic_credential(
        username="ubuntu", password="secret")
    factory = BasicSocketDatabaseConnectionFactory(
        "socket-profile", dbprofile=profile, credential=credential)
    rtnval = (profile, credential, factory)
    return rtnval


def _establish_tcp_env() -> Tuple["mock.MagicMock", "mock.MagicMock",
                                   BasicTcpDatabaseConnectionFactory]:
    """
        Replicates the original
        ``TestBasicTcpDatabaseConnectionFactory.setUp`` by building a fresh TCP
        profile, basic credential, and factory.

        :returns: A ``(profile, credential, factory)`` tuple.
    """
    profile = _make_tcp_profile(
        host="db.example.com",
        port=5432,
        dbname="primary_db")
    credential = _make_basic_credential(
        username="ubuntu", password="secret")
    factory = BasicTcpDatabaseConnectionFactory(
        "tcp-profile", dbprofile=profile, credential=credential)
    rtnval = (profile, credential, factory)
    return rtnval


def _establish_create_env() -> Dict[str, object]:
    """
        Replicates the original ``TestCreateDatabaseConnectionFactory.setUp``
        by snapshotting and clearing the module-level factory cache so that
        tests do not share cached state.

        :returns: The snapshot of the previous factory cache, to be restored
            during cleanup.
    """
    previous_cache = dict(dbconnection.DATABASE_CONNECTION_FACTORIES)
    dbconnection.DATABASE_CONNECTION_FACTORIES.clear()
    rtnval = previous_cache
    return rtnval


def _restore_create_env(previous_cache: Dict[str, object]) -> None:
    """
        Replicates the original ``TestCreateDatabaseConnectionFactory.tearDown``
        by restoring the previously snapshot factory cache.

        :param previous_cache: The snapshot to restore into the module-level
            factory cache.
    """
    dbconnection.DATABASE_CONNECTION_FACTORIES.clear()
    dbconnection.DATABASE_CONNECTION_FACTORIES.update(previous_cache)
    return


def test_constructor_stores_inputs() -> None:
    """
        Verify that constructor arguments are exposed via the corresponding
        properties.
    """
    profile, credential = _establish_base_env()

    factory = DatabaseConnectionFactory(
        "profile-x", dbprofile=profile, credential=credential)

    assert factory.profile_name == "profile-x"
    assert factory.dbprofile is profile
    assert factory.credential is credential
    return


def test_create_engine_raises_not_implemented() -> None:
    """
        Verify that the base ``create_engine`` raises :class:`NotImplementedError`.
    """
    profile, credential = _establish_base_env()

    factory = DatabaseConnectionFactory(
        "profile-x", dbprofile=profile, credential=credential)

    raised = False
    try:
        factory.create_engine()
    except NotImplementedError:
        raised = True
    assert raised
    return


def test_get_connection_scheme_postgresql_socket() -> None:
    """
        Verify that postgresql socket profiles resolve to the
        ``postgresql+psycopg2`` SQLAlchemy scheme.
    """
    profile, credential, factory = _establish_socket_env()

    scheme = factory.get_connection_scheme()
    assert scheme == "postgresql+psycopg2"
    return


def test_get_connection_scheme_unknown_raises_socket() -> None:
    """
        Verify that an unsupported socket dbtype raises ``ConfigurationError``
        rather than silently yielding a ``None`` scheme (which would later
        produce a malformed ``None://`` connection string).
    """
    profile, credential, factory = _establish_socket_env()

    unknown_profile = _make_socket_profile(dbtype="mysql")
    factory = BasicSocketDatabaseConnectionFactory(
        "socket-profile", dbprofile=unknown_profile, credential=credential)

    raised = False
    try:
        factory.get_connection_scheme()
    except ConfigurationError:
        raised = True

    assert raised
    return


def test_format_connection_string_uses_profile_dbname() -> None:
    """
        Verify that the connection string falls back to the profile
        ``dbname`` when no override is supplied.
    """
    profile, credential, factory = _establish_socket_env()

    conn_str = factory.format_connection_string()
    expected = "postgresql+psycopg2://ubuntu:secret@/primary_db?host=/var/run/postgresql"
    assert conn_str == expected
    return


def test_format_connection_string_uses_override_dbname() -> None:
    """
        Verify that an explicit ``dbname`` override is honored.
    """
    profile, credential, factory = _establish_socket_env()

    conn_str = factory.format_connection_string(dbname="alternate_db")
    expected = "postgresql+psycopg2://ubuntu:secret@/alternate_db?host=/var/run/postgresql"
    assert conn_str == expected
    return


def test_format_connection_string_with_non_basic_credential_raises() -> None:
    """
        Verify that supplying a non-:class:`BasicCredential` raises
        :class:`ConfigurationError`.
    """
    profile, credential, factory = _establish_socket_env()

    bad_credential = _make_non_basic_credential()
    factory = BasicSocketDatabaseConnectionFactory(
        "socket-profile", dbprofile=profile, credential=bad_credential)

    raised = False
    try:
        factory.format_connection_string()
    except ConfigurationError:
        raised = True
    assert raised
    return


def test_create_engine_invokes_sqlalchemy_create_engine_socket() -> None:
    """
        Verify that ``create_engine`` builds the connection string and
        forwards it to ``sqlalchemy.create_engine`` with ``echo``.
    """
    profile, credential, factory = _establish_socket_env()

    sentinel_engine = mock.MagicMock(name="sentinel_engine")

    with mock.patch.object(dbconnection, "create_engine", return_value=sentinel_engine) as mock_ce:
        engine = factory.create_engine(dbname="alternate_db", echo=False)

    expected_conn = "postgresql+psycopg2://ubuntu:secret@/alternate_db?host=/var/run/postgresql"
    mock_ce.assert_called_once_with(expected_conn, echo=False)
    assert engine is sentinel_engine
    return


def test_create_engine_with_non_basic_credential_raises() -> None:
    """
        Verify that ``create_engine`` raises when the credential is not a
        :class:`BasicCredential`.
    """
    profile, credential, factory = _establish_socket_env()

    bad_credential = _make_non_basic_credential()
    factory = BasicSocketDatabaseConnectionFactory(
        "socket-profile", dbprofile=profile, credential=bad_credential)

    raised = False
    try:
        factory.create_engine()
    except ConfigurationError:
        raised = True
    assert raised
    return


def test_create_engine_falls_back_to_profile_dbname() -> None:
    """
        Verify that omitting ``dbname`` causes the factory to use the
        profile-supplied database name.
    """
    profile, credential, factory = _establish_socket_env()

    sentinel_engine = mock.MagicMock(name="sentinel_engine")

    with mock.patch.object(dbconnection, "create_engine", return_value=sentinel_engine) as mock_ce:
        factory.create_engine()

    called_args, called_kwargs = mock_ce.call_args
    assert "primary_db" in called_args[0]
    assert called_kwargs.get("echo") == True
    return


def test_get_connection_scheme_postgresql_tcp() -> None:
    """
        Verify that postgresql TCP profiles resolve to the
        ``postgresql+psycopg2`` SQLAlchemy scheme.
    """
    profile, credential, factory = _establish_tcp_env()

    scheme = factory.get_connection_scheme()
    assert scheme == "postgresql+psycopg2"
    return


def test_get_connection_scheme_unknown_raises_tcp() -> None:
    """
        Verify that an unsupported TCP dbtype raises ``ConfigurationError``
        rather than silently yielding a ``None`` scheme.
    """
    profile, credential, factory = _establish_tcp_env()

    unknown_profile = _make_tcp_profile(dbtype="mysql")
    factory = BasicTcpDatabaseConnectionFactory(
        "tcp-profile", dbprofile=unknown_profile, credential=credential)

    raised = False
    try:
        factory.get_connection_scheme()
    except ConfigurationError:
        raised = True

    assert raised
    return


def test_format_connection_string_with_override_dbname() -> None:
    """
        Verify TCP connection-string formatting honors a ``dbname`` override.
    """
    profile, credential, factory = _establish_tcp_env()

    conn_str = factory.format_connection_string(dbname="alternate_db")
    expected = "postgresql+psycopg2://ubuntu:secret@db.example.com:5432/alternate_db"
    assert conn_str == expected
    return


def test_format_connection_string_default_dbname_uses_profile() -> None:
    """
        Verify TCP connection-string formatting falls back to the profile
        ``dbname`` when no override is supplied.
    """
    profile, credential, factory = _establish_tcp_env()

    conn_str = factory.format_connection_string()
    expected = "postgresql+psycopg2://ubuntu:secret@db.example.com:5432/primary_db"
    assert conn_str == expected
    return


def test_format_connection_string_with_non_basic_credential_returns_none() -> None:
    """
        Verify the TCP factory returns ``None`` (per current implementation)
        when the credential is not a :class:`BasicCredential`.
    """
    profile, credential, factory = _establish_tcp_env()

    bad_credential = _make_non_basic_credential()
    factory = BasicTcpDatabaseConnectionFactory(
        "tcp-profile", dbprofile=profile, credential=bad_credential)

    conn_str = factory.format_connection_string()
    assert conn_str is None
    return


def test_create_engine_invokes_sqlalchemy_create_engine_tcp() -> None:
    """
        Verify that the TCP factory ``create_engine`` builds the connection
        string and forwards it to ``sqlalchemy.create_engine``.
    """
    profile, credential, factory = _establish_tcp_env()

    sentinel_engine = mock.MagicMock(name="sentinel_engine")

    with mock.patch.object(dbconnection, "create_engine", return_value=sentinel_engine) as mock_ce:
        engine = factory.create_engine(dbname="alternate_db", echo=False)

    expected_conn = "postgresql+psycopg2://ubuntu:secret@db.example.com:5432/alternate_db"
    mock_ce.assert_called_once_with(expected_conn, echo=False)
    assert engine is sentinel_engine
    return


def test_socket_profile_creates_socket_factory() -> None:
    """
        Verify that a ``basic-socket`` category profile yields a
        :class:`BasicSocketDatabaseConnectionFactory`.
    """
    previous_cache = _establish_create_env()
    try:
        profile = _make_socket_profile(identifier="socket-1")
        credential = _make_basic_credential()
        cred_manager = _make_credential_manager(
            credential_name=profile.credential, credential=credential)

        factory = create_database_connection_factory(profile, cred_manager)

        assert isinstance(factory, BasicSocketDatabaseConnectionFactory)
        assert factory.profile_name == "socket-1"
    finally:
        _restore_create_env(previous_cache)
    return


def test_tcp_profile_creates_tcp_factory() -> None:
    """
        Verify that a ``basic-tcp`` category profile yields a
        :class:`BasicTcpDatabaseConnectionFactory`.
    """
    previous_cache = _establish_create_env()
    try:
        profile = _make_tcp_profile(identifier="tcp-1")
        credential = _make_basic_credential()
        cred_manager = _make_credential_manager(
            credential_name=profile.credential, credential=credential)

        factory = create_database_connection_factory(profile, cred_manager)

        assert isinstance(factory, BasicTcpDatabaseConnectionFactory)
        assert factory.profile_name == "tcp-1"
    finally:
        _restore_create_env(previous_cache)
    return


def test_unknown_category_raises_configuration_error() -> None:
    """
        Verify that an unsupported profile category raises
        :class:`ConfigurationError`.
    """
    previous_cache = _establish_create_env()
    try:
        profile = _make_socket_profile(identifier="weird-1")
        profile.category = "weird-category"
        credential = _make_basic_credential()
        cred_manager = _make_credential_manager(
            credential_name=profile.credential, credential=credential)

        raised = False
        try:
            create_database_connection_factory(profile, cred_manager)
        except ConfigurationError:
            raised = True
        assert raised
    finally:
        _restore_create_env(previous_cache)
    return


def test_factory_is_cached_by_profile_identifier() -> None:
    """
        Verify that repeated calls with the same profile identifier return
        the same cached factory instance.
    """
    previous_cache = _establish_create_env()
    try:
        profile = _make_socket_profile(identifier="cached-1")
        credential = _make_basic_credential()
        cred_manager = _make_credential_manager(
            credential_name=profile.credential, credential=credential)

        first = create_database_connection_factory(profile, cred_manager)
        second = create_database_connection_factory(profile, cred_manager)

        assert first is second
    finally:
        _restore_create_env(previous_cache)
    return
