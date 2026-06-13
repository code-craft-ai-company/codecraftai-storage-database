"""
.. module:: test_dbio
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Testbase tests for :mod:`ccai.storage.database.dbio`.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"

from unittest import mock

from ccai.storage.database import dbio
from ccai.storage.database.dbconnection import DatabaseConnectionFactory


def _make_conn_factory(*, conn_str: str = "postgresql+psycopg2://u:p@/db?host=/sock",
                       engine: "mock.MagicMock" = None) -> "mock.MagicMock":
    """
        Build a stand-in :class:`DatabaseConnectionFactory` mock.

        :param conn_str: Value returned by ``format_connection_string``.
        :param engine: Engine mock returned by ``create_engine``. When ``None``
            a fresh ``MagicMock`` is allocated.

        :returns: Mock object with ``spec=DatabaseConnectionFactory``.
    """
    if engine is None:
        engine = mock.MagicMock(name="fake_engine")

    factory = mock.MagicMock(spec=DatabaseConnectionFactory)
    factory.format_connection_string.return_value = conn_str
    factory.create_engine.return_value = engine
    return factory


def _make_db_profile(*, dbname: str = "primary_db") -> "mock.MagicMock":
    """
        Build a stand-in database profile.

        :param dbname: Database name exposed by the profile.

        :returns: Mock profile object with ``dbname`` set.
    """
    profile = mock.MagicMock()
    profile.dbname = dbname
    return profile


def test_delegates_to_sqlalchemy_utils() -> None:
    """
        Verify that :func:`database_exists` forwards the formatted connection
        string to ``sqlalchemy_utils.database_exists`` and returns the result.
    """
    conn_factory = _make_conn_factory(conn_str="conn-string-A")

    with mock.patch.object(dbio, "sqlutils_database_exists", return_value=True) as mock_exists:
        result = dbio.database_exists(conn_factory, dbname="alpha")

    conn_factory.format_connection_string.assert_called_once_with(dbname="alpha")
    mock_exists.assert_called_once_with("conn-string-A")
    assert result
    return


def test_returns_false_when_database_missing() -> None:
    """
        Verify that :func:`database_exists` returns ``False`` when the
        underlying utility reports the database does not exist.
    """
    conn_factory = _make_conn_factory()

    with mock.patch.object(dbio, "sqlutils_database_exists", return_value=False):
        result = dbio.database_exists(conn_factory)

    assert not result
    return


def test_passes_none_dbname_through() -> None:
    """
        Verify that omitting ``dbname`` results in ``None`` being passed to
        ``format_connection_string``.
    """
    conn_factory = _make_conn_factory()

    with mock.patch.object(dbio, "sqlutils_database_exists", return_value=True):
        dbio.database_exists(conn_factory)

    conn_factory.format_connection_string.assert_called_once_with(dbname=None)
    return


def test_creates_database_without_metadata() -> None:
    """
        Verify that ``database_create`` only invokes the create helper when
        no metadata is supplied.
    """
    conn_factory = _make_conn_factory(conn_str="conn-string-B")

    with mock.patch.object(dbio, "sqlutils_create_database") as mock_create:
        dbio.database_create(conn_factory, dbname="bravo")

    conn_factory.format_connection_string.assert_called_once_with(dbname="bravo")
    mock_create.assert_called_once_with("conn-string-B")
    conn_factory.create_engine.assert_not_called()
    return


def test_creates_schema_when_metadata_supplied() -> None:
    """
        Verify that supplying ``dbmetadata`` causes a SQLAlchemy engine to
        be built and ``MetaData.create_all`` to be invoked against it.
    """
    engine = mock.MagicMock(name="engine")
    conn_factory = _make_conn_factory(engine=engine)
    metadata = mock.MagicMock(name="metadata")

    with mock.patch.object(dbio, "sqlutils_create_database") as mock_create:
        dbio.database_create(conn_factory, dbname="charlie", dbmetadata=metadata)

    mock_create.assert_called_once()
    conn_factory.create_engine.assert_called_once_with(dbname="charlie")
    metadata.create_all.assert_called_once_with(engine)
    return


def test_creates_when_database_does_not_exist() -> None:
    """
        Verify the happy-path where the database does not exist: it is
        created and the schema is realized via ``orm_metadata.create_all``.
    """
    engine = mock.MagicMock(name="engine")
    conn_factory = _make_conn_factory(engine=engine)
    cred_manager = mock.MagicMock(name="cred_manager")
    profile = _make_db_profile(dbname="delta_db")
    orm_metadata = mock.MagicMock(name="orm_metadata")

    with mock.patch.object(dbio, "create_database_connection_factory", return_value=conn_factory) as mock_create_factory, \
         mock.patch.object(dbio, "database_exists", return_value=False) as mock_exists, \
         mock.patch.object(dbio, "database_create") as mock_create_db, \
         mock.patch.object(dbio, "sqlutils_drop_database") as mock_drop:
        dbio.create_network_attached_database(
            profile, cred_manager, orm_metadata, reset=False)

    mock_create_factory.assert_called_once_with(profile, cred_manager)
    mock_exists.assert_called_once_with(conn_factory, "delta_db")
    mock_create_db.assert_called_once_with(conn_factory, "delta_db")
    mock_drop.assert_not_called()
    conn_factory.create_engine.assert_called_once_with(dbname="delta_db", echo=True)
    orm_metadata.create_all.assert_called_once_with(engine, checkfirst=True)
    return


def test_skips_creation_when_database_already_exists() -> None:
    """
        Verify that an existing database is not re-created when ``reset`` is
        ``False``.
    """
    engine = mock.MagicMock(name="engine")
    conn_factory = _make_conn_factory(engine=engine)
    cred_manager = mock.MagicMock(name="cred_manager")
    profile = _make_db_profile(dbname="echo_db")
    orm_metadata = mock.MagicMock(name="orm_metadata")

    with mock.patch.object(dbio, "create_database_connection_factory", return_value=conn_factory), \
         mock.patch.object(dbio, "database_exists", return_value=True), \
         mock.patch.object(dbio, "database_create") as mock_create_db, \
         mock.patch.object(dbio, "sqlutils_drop_database") as mock_drop:
        dbio.create_network_attached_database(
            profile, cred_manager, orm_metadata, reset=False)

    mock_create_db.assert_not_called()
    mock_drop.assert_not_called()
    orm_metadata.create_all.assert_called_once_with(engine, checkfirst=True)
    return


def test_drops_and_recreates_when_reset_true_and_exists() -> None:
    """
        Verify that ``reset=True`` causes the existing database to be
        dropped and re-created.
    """
    engine = mock.MagicMock(name="engine")
    conn_factory = _make_conn_factory(conn_str="conn-string-F", engine=engine)
    cred_manager = mock.MagicMock(name="cred_manager")
    profile = _make_db_profile(dbname="foxtrot_db")
    orm_metadata = mock.MagicMock(name="orm_metadata")

    # database_exists is consulted twice: once for the reset branch, once
    # to decide whether to create the database. The first call returns
    # True (database exists, drop it). The second call returns False so
    # that database_create runs.
    exists_returns = [True, False]

    with mock.patch.object(dbio, "create_database_connection_factory", return_value=conn_factory), \
         mock.patch.object(dbio, "database_exists", side_effect=exists_returns), \
         mock.patch.object(dbio, "database_create") as mock_create_db, \
         mock.patch.object(dbio, "sqlutils_drop_database") as mock_drop:
        dbio.create_network_attached_database(
            profile, cred_manager, orm_metadata, reset=True)

    mock_drop.assert_called_once_with("conn-string-F")
    mock_create_db.assert_called_once_with(conn_factory, "foxtrot_db")
    return


def test_raises_when_factory_is_none() -> None:
    """
        Verify that a ``None`` factory result causes a
        :class:`ConfigurationError`.
    """
    from ccai.errors.exceptions import ConfigurationError

    cred_manager = mock.MagicMock(name="cred_manager")
    profile = _make_db_profile()
    # The error path indexes profile["name"], so make __getitem__ work.
    profile.__getitem__.return_value = "named-profile"
    orm_metadata = mock.MagicMock(name="orm_metadata")

    with mock.patch.object(dbio, "create_database_connection_factory", return_value=None):
        raised = False
        try:
            dbio.create_network_attached_database(
                profile, cred_manager, orm_metadata)
        except ConfigurationError:
            raised = True

    assert raised
    return


def test_returns_engine_for_profile() -> None:
    """
        Verify that the function returns the engine produced by the
        connection factory for the profile's database.
    """
    engine = mock.MagicMock(name="engine")
    conn_factory = _make_conn_factory(engine=engine)
    cred_manager = mock.MagicMock(name="cred_manager")
    profile = _make_db_profile(dbname="golf_db")

    with mock.patch.object(dbio, "create_database_connection_factory", return_value=conn_factory) as mock_create_factory:
        result = dbio.open_network_attached_database(profile, cred_manager)

    mock_create_factory.assert_called_once_with(profile, cred_manager)
    conn_factory.create_engine.assert_called_once_with(dbname="golf_db", echo=True)
    assert result is engine
    return


def test_open_raises_when_factory_is_none() -> None:
    """
        Verify that a ``None`` factory result causes a
        :class:`ConfigurationError`.
    """
    from ccai.errors.exceptions import ConfigurationError

    cred_manager = mock.MagicMock(name="cred_manager")
    profile = _make_db_profile()
    profile.__getitem__.return_value = "named-profile"

    with mock.patch.object(dbio, "create_database_connection_factory", return_value=None):
        raised = False
        try:
            dbio.open_network_attached_database(profile, cred_manager)
        except ConfigurationError:
            raised = True

    assert raised
    return


def test_truncates_tables_when_database_exists() -> None:
    """
        Verify that the function opens a transaction and issues a single
        TRUNCATE statement that names all the metadata tables in reverse
        sort order.
    """
    # Build a connection / transaction stack.
    connection = mock.MagicMock(name="connection")
    transaction = mock.MagicMock(name="transaction")
    connection.begin.return_value = transaction
    engine = mock.MagicMock(name="engine")
    engine.connect.return_value = connection

    conn_factory = _make_conn_factory(engine=engine)
    cred_manager = mock.MagicMock(name="cred_manager")
    profile = _make_db_profile(dbname="hotel_db")

    # Build mock tables; reversed(sorted_tables) feeds the TRUNCATE call.
    table_a = mock.MagicMock()
    table_a.name = "table_a"
    table_b = mock.MagicMock()
    table_b.name = "table_b"
    orm_metadata = mock.MagicMock(name="orm_metadata")
    orm_metadata.sorted_tables = [table_a, table_b]

    with mock.patch.object(dbio, "create_database_connection_factory", return_value=conn_factory), \
         mock.patch.object(dbio, "database_exists", return_value=True):
        dbio.reset_network_attached_database(profile, cred_manager, orm_metadata)

    engine.connect.assert_called_once_with()
    connection.begin.assert_called_once_with()
    # SQLAlchemy 2.0 requires an executable; the statement must be a ``text()``
    # clause (a raw str raises ObjectNotExecutableError), and its SQL text must
    # name the tables in reverse sort order.
    connection.execute.assert_called_once()
    executed_statement = connection.execute.call_args.args[0]
    assert not isinstance(executed_statement, str)
    assert str(executed_statement) == "TRUNCATE table_b,table_a RESTART IDENTITY;"
    transaction.commit.assert_called_once_with()
    connection.close.assert_called_once_with()
    return


def test_noop_when_database_does_not_exist() -> None:
    """
        Verify that the reset is skipped when the database does not exist.
    """
    engine = mock.MagicMock(name="engine")
    conn_factory = _make_conn_factory(engine=engine)
    cred_manager = mock.MagicMock(name="cred_manager")
    profile = _make_db_profile(dbname="india_db")
    orm_metadata = mock.MagicMock(name="orm_metadata")

    with mock.patch.object(dbio, "create_database_connection_factory", return_value=conn_factory), \
         mock.patch.object(dbio, "database_exists", return_value=False):
        dbio.reset_network_attached_database(profile, cred_manager, orm_metadata)

    engine.connect.assert_not_called()
    return


def test_reset_raises_when_factory_is_none() -> None:
    """
        Verify that a ``None`` factory result causes a
        :class:`ConfigurationError`.
    """
    from ccai.errors.exceptions import ConfigurationError

    cred_manager = mock.MagicMock(name="cred_manager")
    profile = _make_db_profile()
    profile.__getitem__.return_value = "named-profile"
    orm_metadata = mock.MagicMock(name="orm_metadata")

    with mock.patch.object(dbio, "create_database_connection_factory", return_value=None):
        raised = False
        try:
            dbio.reset_network_attached_database(profile, cred_manager, orm_metadata)
        except ConfigurationError:
            raised = True

    assert raised
    return
