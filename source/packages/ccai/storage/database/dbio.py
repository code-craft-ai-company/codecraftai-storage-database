"""
.. module:: dbio
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Contains helper functions for working with specific databases

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []
__version__ = "1.0.0"


from typing import Optional


import contextlib
import logging

from sqlalchemy import text
from sqlalchemy.engine.base import Engine as SqlEngine
from sqlalchemy.sql.schema import MetaData

from sqlalchemy_utils import database_exists as sqlutils_database_exists
from sqlalchemy_utils import create_database as sqlutils_create_database
from sqlalchemy_utils import drop_database as sqlutils_drop_database

from ccai.errors.exceptions import ConfigurationError

from ccai.credentials.credentialmanager import CredentialManager

from ccai.dataprofiles.databasebasicsocketprofile import DatabaseBasicSocketProfile

from ccai.storage.database.dbconnection import DatabaseConnectionFactory, create_database_connection_factory


logger = logging.getLogger()


def database_exists(conn_factory: DatabaseConnectionFactory, dbname: Optional[str]=None) -> bool:
    """
        Check if the specified database exists.

        :param conn_factory: Factory used to construct the database connection string.
        :param dbname: Optional database name override for the profile default.

        :returns: ``True`` if the database exists, otherwise ``False``.
    """
    conn_str = conn_factory.format_connection_string(dbname=dbname)

    exists = sqlutils_database_exists(conn_str)

    return exists


def database_create(conn_factory: DatabaseConnectionFactory, dbname: Optional[str]=None, dbmetadata: Optional[MetaData]=None):
    """
        Create the specified database.

        :param conn_factory: Factory used to construct the database connection string.
        :param dbname: Optional database name override for the profile default.
        :param dbmetadata: SQLAlchemy metadata describing the schema to realize.
    """

    conn_str = conn_factory.format_connection_string(dbname=dbname)

    sqlutils_create_database(conn_str)

    if dbmetadata is not None:
        engine = conn_factory.create_engine(dbname=dbname)
        dbmetadata.create_all(engine)

    return


def create_network_attached_database(db_profile: DatabaseBasicSocketProfile, cred_manager: CredentialManager, orm_metadata: MetaData, *, reset: bool = False):
    """
        Create a network attached database if it does not exist, optionally resetting it first.

        :param db_profile: Database profile containing the connection configuration.
        :param cred_manager: Credential manager instance for obtaining credentials.
        :param orm_metadata: Object relational mapping used to create database structures.
        :param reset: When ``True`` drop the existing database before creation.

        :raises: ConfigurationError
    """
    db_name = db_profile.dbname

    conn_factory = create_database_connection_factory(db_profile, cred_manager)
    if conn_factory is None:
        db_profile_name = db_profile.identifier
        errmsg = "'create_ccai_enterprise_database' could not get a connection factory for profile={}".format(
            db_profile_name
        )
        raise ConfigurationError(errmsg)

    if reset and database_exists(conn_factory, db_name):
        conn_str = conn_factory.format_connection_string(dbname=db_name)
        sqlutils_drop_database(conn_str)

    if not database_exists(conn_factory, db_name):
        database_create(conn_factory, db_name)

    engine = conn_factory.create_engine(dbname=db_name, echo=True)

    orm_metadata.create_all(engine, checkfirst=True)

    return


def open_network_attached_database(db_profile: DatabaseBasicSocketProfile, cred_manager: CredentialManager) -> SqlEngine:
    """
        Open a network attached database and return a SQLAlchemy engine.

        :param db_profile: Database profile containing the connection configuration.
        :param cred_manager: Credential manager instance for obtaining credentials.

        :returns: SQLAlchemy engine configured for the specified database.
        :raises: ConfigurationError
    """
    dbname = db_profile.dbname

    conn_factory = create_database_connection_factory(db_profile, cred_manager)
    if conn_factory is None:
        db_profile_name = db_profile.identifier
        errmsg = "'open_pychestrate_database' could not get a connection factory for profile={}".format(
            db_profile_name
        )
        raise ConfigurationError(errmsg)

    engine = conn_factory.create_engine(dbname=dbname, echo=True)

    return engine


def reset_network_attached_database(db_profile: DatabaseBasicSocketProfile, cred_manager: CredentialManager, orm_metadata: MetaData):
    """
        Reset a network attached database by truncating all mapped tables.

        :param db_profile: Database profile containing the connection configuration.
        :param cred_manager: Credential manager instance for obtaining credentials.
        :param orm_metadata: Object relational mapping that identifies the tables to truncate.

        :raises: ConfigurationError
    """
    dbname = db_profile.dbname

    conn_factory = create_database_connection_factory(db_profile, cred_manager)
    if conn_factory is None:
        db_profile_name = db_profile.identifier
        errmsg = "'reset_pychestrate_database' could not get a connection factory for profile={}".format(
            db_profile_name
        )
        raise ConfigurationError(errmsg)

    if database_exists(conn_factory, dbname):
    
        engine = conn_factory.create_engine(dbname=dbname, echo=True)

        with contextlib.closing(engine.connect()) as con:
            trans = con.begin()
            table_names = ','.join(
                table.name for table in reversed(orm_metadata.sorted_tables)
            )
            truncate_statement = text("TRUNCATE {} RESTART IDENTITY;".format(table_names))
            con.execute(truncate_statement)
            trans.commit()

    return
