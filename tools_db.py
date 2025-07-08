"""
This file is part of Giswater
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-
from qgis.PyQt.QtSql import QSqlDatabase, QSqlQueryModel
from qgis.core import QgsCredentials, QgsDataSourceUri, QgsWkbTypes
from qgis.PyQt.QtCore import QSettings

from qgis.utils import iface

from . import lib_vars
from . import tools_log, tools_qt, tools_qgis, tools_pgdao, tools_os


dao = None
dao_db_credentials: dict[str, str] = None
current_user = None


def create_list_for_completer(sql):
    """
    Prepare a list with the necessary items for the completer
        :param sql: Query to be executed, where will we get the list of items (string)
        :return: list_items: List with the result of the query executed (List) ["item1","item2","..."]
    """

    rows = get_rows(sql)
    list_items = []
    if rows:
        for row in rows:
            list_items.append(str(row[0]))
    return list_items


def check_schema(schemaname=None):
    """ Check if selected schema exists """

    if schemaname in (None, 'null', ''):
        schemaname = lib_vars.schema_name

    schemaname = schemaname.replace('"', '')
    sql = "SELECT nspname FROM pg_namespace WHERE nspname = %s"
    params = [schemaname]
    row = get_row(sql, params=params)
    return row


def check_table(tablename, schemaname=None):
    """ Check if selected table exists in selected schema """

    if schemaname in (None, 'null', ''):
        schemaname = lib_vars.schema_name
        if schemaname in (None, 'null', ''):
            get_layer_source_from_credentials('prefer')
            schemaname = lib_vars.schema_name
            if schemaname in (None, 'null', ''):
                return None

    schemaname = schemaname.replace('"', '')
    sql = "SELECT * FROM pg_tables WHERE schemaname = %s AND tablename = %s"
    params = [schemaname, tablename]
    row = get_row(sql, log_info=False, params=params)
    return row


def check_view(viewname, schemaname=None):
    """ Check if selected view exists in selected schema """

    if schemaname in (None, 'null', ''):
        schemaname = lib_vars.schema_name

    schemaname = schemaname.replace('"', '')
    sql = ("SELECT * FROM pg_views "
           "WHERE schemaname = %s AND viewname = %s ")
    params = [schemaname, viewname]
    row = get_row(sql, log_info=False, params=params)
    return row


def check_column(tablename, columname, schemaname=None):
    """ Check if @columname exists table @schemaname.@tablename """

    if schemaname in (None, 'null', ''):
        schemaname = lib_vars.schema_name

    schemaname = schemaname.replace('"', '')
    sql = ("SELECT * FROM information_schema.columns "
           "WHERE table_schema = %s AND table_name = %s AND column_name = %s")
    params = [schemaname, tablename, columname]
    row = get_row(sql, log_info=False, params=params)
    return row


def check_role(role_name, is_admin=None):
    """ Check if @role_name exists """

    sql = f"SELECT * FROM pg_roles WHERE rolname = '{role_name}'"
    row = get_row(sql, log_info=False, is_admin=is_admin)
    return row


def check_role_user(role_name, username=None):
    """ Check if current user belongs to @role_name """

    global current_user  # noqa: F824
    # Check both @role_name and @username exists
    if not check_role(role_name):
        return False

    if username is None:
        username = current_user

    if not check_role(username):
        return False

    sql = ("SELECT pg_has_role('" + username + "', '" + role_name + "', 'MEMBER');")
    row = get_row(sql)
    if row:
        return row[0]
    else:
        return False


def check_super_user(username=None):
    """ Returns True if @username is a superuser """

    global current_user  # noqa: F824
    if username is None:
        username = current_user

    if not check_role(username):
        return False

    sql = f"SELECT usesuper FROM pg_user WHERE usename = '{username}'"
    row = get_row(sql)
    if row:
        return row[0]
    else:
        return False


def check_pg_extension(extension, form_enabled=True):
    sql = f"SELECT extname FROM pg_extension WHERE extname = '{extension}'"
    row = get_row(sql)

    if not row:
        sql = f"SELECT name FROM pg_available_extensions WHERE name = '{extension}'"
        row = get_row(sql)
        if row and form_enabled:
            sql = "set search_path = public;"
            execute_sql(sql)
            sql = f"CREATE EXTENSION IF NOT EXISTS {extension};"
            execute_sql(sql)

            if extension == 'postgis':
                postgis_version = get_postgis_version()
                # Check postGis version
                major_version = postgis_version.split(".")
                if int(major_version[0]) >= 3:
                    sql = "set search_path = public;"
                    execute_sql(sql)
                    sql = "CREATE EXTENSION IF NOT EXISTS postgis_raster;"
                    execute_sql(sql)
            return True, None
        elif form_enabled:
            message = (f"Unable to create '{extension}' extension. "
                      f"Packages must be installed, consult your administrator.")
            return False, message

    return True, None


def get_current_user():
    """ Get current user connected to database """

    global current_user  # noqa: F824
    if current_user:
        return current_user

    sql = "SELECT current_user"
    row = get_row(sql)
    cur_user = ""
    if row:
        cur_user = str(row[0])
    current_user = cur_user
    return cur_user


def get_columns_list(tablename, schemaname=None):
    """ Return list of all columns in @tablename """

    if schemaname in (None, 'null', ''):
        schemaname = lib_vars.schema_name

    schemaname = schemaname.replace('"', '')
    sql = ("SELECT column_name FROM information_schema.columns "
           "WHERE table_schema = %s AND table_name = %s "
           "ORDER BY ordinal_position")
    params = [schemaname, tablename]
    column_names = get_rows(sql, params=params)
    return column_names


def get_srid(tablename, schemaname=None):
    """ Find SRID of selected @tablename """

    if schemaname in (None, 'null', ''):
        schemaname = lib_vars.schema_name

    schemaname = schemaname.replace('"', '')
    srid = None
    sql = "SELECT Find_SRID(%s, %s, 'the_geom');"
    params = [schemaname, tablename]
    row = get_row(sql, params=params)
    if row:
        srid = row[0]

    return srid


def set_database_connection():
    """ Set database connection """

    global dao  # noqa: F824
    global current_user  # noqa: F824
    dao = None
    lib_vars.session_vars['last_error'] = None
    lib_vars.session_vars['logged_status'] = False
    current_user = None

    layer_source, not_version = get_layer_source_from_credentials('prefer')
    if layer_source:
        if layer_source['service'] is None and \
                (layer_source['db'] is None or layer_source['host'] is None or layer_source['user'] is None
                 or layer_source['password'] is None or layer_source['port'] is None):
            return False, not_version, layer_source
    else:
        return False, not_version, layer_source

    lib_vars.session_vars['logged_status'] = True

    return True, not_version, layer_source


def check_db_connection():
    """ Check database connection. Reconnect if needed """

    global dao  # noqa: F824
    opened = True
    try:
        was_closed = dao.check_connection()
        if was_closed:
            msg = "Database connection was closed and reconnected"
            tools_log.log_warning(msg)
            opened = lib_vars.qgis_db_credentials.open()
            if not opened:
                msg = lib_vars.qgis_db_credentials.lastError().databaseText()
                msg = "Database connection error ({0    }): {1}"
                msg_params = ("QSqlDatabase", msg,)
                tools_log.log_warning(msg, msg_params=msg_params)
    except Exception as e:
        msg = "{0} Exception: {1}"
        msg_params = ("check_db_connection", e,)
        tools_log.log_warning(msg, msg_params=msg_params)
    finally:
        return opened


def get_pg_version():
    """ Get PostgreSQL version (integer value) """

    pg_version = None
    sql = "SELECT current_setting('server_version_num');"
    row = get_row(sql)
    if row:
        pg_version = row[0]

    return pg_version


def connect_to_database(host, port, db, user, pwd, sslmode):
    """ Connect to database with selected parameters """

    global dao  # noqa: F824
    global current_user  # noqa: F824
    # Check if selected parameters is correct
    if None in (host, port, db, user, pwd):
        message = "Database connection error. Please check your connection parameters."
        lib_vars.session_vars['last_error'] = tools_qt.tr(message)
        return False

    # Update current user
    current_user = user

    # QSqlDatabase connection for Table Views
    status = create_qsqldatabase_connection(host, port, db, user, pwd)
    if not status:
        return False
    lib_vars.last_db_credentials = {'host': host, 'port': port, 'db': db, 'user': user, 'pwd': pwd}

    # psycopg2 connection
    dao = tools_pgdao.GwPgDao()
    dao.set_params(host, port, db, user, pwd, sslmode)
    status = dao.init_db()
    msg = "PostgreSQL PID: {0}"
    msg_params = (dao.pid,)
    tools_log.log_info(msg, msg_params=msg_params)
    if not status:
        msg = "Database connection error (psycopg2). Please open plugin log file to get more details"
        lib_vars.session_vars['last_error'] = tools_qt.tr(msg)
        tools_log.log_warning(str(dao.last_error))
        return False

    return status


def create_qsqldatabase_connection(host, port, db, user, pwd):

    # QSqlDatabase connection for Table Views
    lib_vars.qgis_db_credentials = QSqlDatabase.addDatabase("QPSQL", lib_vars.plugin_name)
    lib_vars.qgis_db_credentials.setHostName(host)
    if port != '':
        lib_vars.qgis_db_credentials.setPort(int(port))
    lib_vars.qgis_db_credentials.setDatabaseName(db)
    lib_vars.qgis_db_credentials.setUserName(user)
    lib_vars.qgis_db_credentials.setPassword(pwd)
    status = lib_vars.qgis_db_credentials.open()
    if not status:
        msg = "Database connection error (QSqlDatabase). Please open plugin log file to get more details"
        lib_vars.session_vars['last_error'] = tools_qt.tr(msg)
        details = lib_vars.qgis_db_credentials.lastError().databaseText()
        tools_log.log_warning(str(details))
        return False
    return status


def reset_qsqldatabase_connection(dialog=iface):
    if not lib_vars.last_db_credentials:
        return False

    host = lib_vars.last_db_credentials['host']
    port = lib_vars.last_db_credentials['port']
    db = lib_vars.last_db_credentials['db']
    user = lib_vars.last_db_credentials['user']
    pwd = lib_vars.last_db_credentials['pwd']
    QSqlDatabase.removeDatabase(lib_vars.plugin_name)
    create_qsqldatabase_connection(host, port, db, user, pwd)
    msg = "Database connection reset, please try again"
    tools_qgis.show_warning(msg, dialog=dialog)


def fill_table_by_query(qtable, query):
    """
    :param qtable: QTableView to show
    :param query: query to set model
    """
    model = QSqlQueryModel()
    model.setQuery(query, db=lib_vars.qgis_db_credentials)
    qtable.setModel(model)
    qtable.show()

    # Check for errors
    if model.lastError().isValid():
        if 'Unable to find table' in model.lastError().text():
            reset_qsqldatabase_connection()
        else:
            tools_qgis.show_warning(model.lastError().text())


def connect_to_database_service(service, sslmode=None, conn_info=None):
    """ Connect to database trough selected service
    This service must exist in file pg_service.conf """

    global dao  # noqa: F824
    conn_string = f"service='{service}'"
    if sslmode:
        conn_string += f" sslmode={sslmode}"

    # Get credentials from .pg_service.conf
    credentials = tools_os.manage_pg_service(service)
    if all([credentials['host'], credentials['port'], credentials['dbname']]) and \
            None in [credentials['user'], credentials['password']]:
        if conn_info is None:
            conn_info = f"service='{service}'"
        (success, credentials['user'], credentials['password']) = \
                QgsCredentials.instance().get(
                    conn_info,
                    credentials['user'],
                    credentials['password'],
                    f"Please enter the credentials for connection '{service}'"
                )

        # Put the credentials back (for yourself and the provider), as QGIS removes it when you "get" it
        QgsCredentials.instance().put(conn_info, credentials['user'], credentials['password'])

    if credentials:
        status = connect_to_database(credentials['host'], credentials['port'], credentials['dbname'],
                                     credentials['user'], credentials['password'], credentials['sslmode'])
    else:
        # Try to connect using name defined in service file
        # QSqlDatabase connection
        lib_vars.qgis_db_credentials = QSqlDatabase.addDatabase("QPSQL", lib_vars.plugin_name)
        lib_vars.qgis_db_credentials.setConnectOptions(conn_string)
        status = lib_vars.qgis_db_credentials.open()
        if not status:
            msg = "Service database connection error (QSqlDatabase). Please open plugin log file to get more details"
            lib_vars.session_vars['last_error'] = tools_qt.tr(msg)
            details = lib_vars.qgis_db_credentials.lastError().databaseText()
            tools_log.log_warning(str(details))
            return False, credentials

        # psycopg2 connection
        dao = tools_pgdao.GwPgDao()
        dao.set_conn_string(conn_string)
        status = dao.init_db()
        msg = "PostgreSQL PID: {0}"
        msg_params = (dao.pid,)
        tools_log.log_info(msg, msg_params=msg_params)
        if not status:
            msg = "Service database connection error (psycopg2). Please open plugin log file to get more details"
            lib_vars.session_vars['last_error'] = tools_qt.tr(msg)
            tools_log.log_warning(str(dao.last_error))
            return False, credentials

    return status, credentials


def get_postgis_version():
    """ Get Postgis version (integer value) """

    postgis_version = None
    postgis_extension = check_pg_extension('postgis')

    if postgis_extension:
        sql = "SELECT postgis_lib_version()"
        row = get_row(sql)
        if row:
            postgis_version = row[0]

    return postgis_version


def get_pgrouting_version():
    """ Get pgRouting version (integer value) """

    pgrouting_version = None
    pgrouting_extension = check_pg_extension('pgrouting')

    if pgrouting_extension:
        sql = "SELECT * FROM pgr_version()"
        row = get_row(sql)
        if row:
            pgrouting_version = row[0]

    return pgrouting_version


def get_row(sql, log_info=True, log_sql=False, commit=True, params=None, aux_conn=None, is_admin=None, is_thread=False):
    """ Execute SQL. Check its result in log tables, and show it to the user """

    global dao  # noqa: F824
    if dao is None:
        msg = "The connection to the database is broken."
        tools_log.log_warning(msg, parameter=sql)
        return None
    sql = _get_sql(sql, log_sql, params)
    row = dao.get_row(sql, commit, aux_conn=aux_conn)
    lib_vars.session_vars['last_error'] = dao.last_error

    if not row and not is_admin:
        # Check if any error has been raised
        if lib_vars.session_vars['last_error'] and not is_thread:
            tools_qt.manage_exception_db(lib_vars.session_vars['last_error'], sql)
        elif lib_vars.session_vars['last_error'] is None and log_info:
            msg = "Any record found"
            tools_log.log_info(msg, parameter=sql, stack_level_increase=1)

    return row


def get_rows(sql, log_info=True, log_sql=False, commit=True, params=None, add_empty_row=False, is_thread=False,
             aux_conn=None):
    """ Execute SQL. Check its result in log tables, and show it to the user """

    global dao  # noqa: F824
    if dao is None:
        msg = "The connection to the database is broken."
        tools_log.log_warning(msg, parameter=sql)
        return None
    sql = _get_sql(sql, log_sql, params)
    rows = None
    rows2 = dao.get_rows(sql, commit, aux_conn=aux_conn)
    lib_vars.session_vars['last_error'] = dao.last_error
    if not rows2:
        # Check if any error has been raised
        if lib_vars.session_vars['last_error'] and not is_thread:
            tools_qt.manage_exception_db(lib_vars.session_vars['last_error'], sql)
        elif lib_vars.session_vars['last_error'] is None and log_info:
            msg = "Any record found"
            tools_log.log_info(msg, parameter=sql, stack_level_increase=1)
    else:
        if add_empty_row:
            rows = [('', '')]
            rows.extend(rows2)
        else:
            rows = rows2

    return rows


def get_values_from_catalog(table_name, typevalue, order_by='id'):

    sql = (f"SELECT id, idval"
           f" FROM {table_name}"
           f" WHERE typevalue = '{typevalue}'"
           f" ORDER BY {order_by}")
    rows = get_rows(sql)
    return rows


def execute_sql(sql, log_sql=False, log_error=False, commit=True, filepath=None, is_thread=False, show_exception=True,
                aux_conn=None):
    """ Execute SQL. Check its result in log tables, and show it to the user """

    global dao  # noqa: F824
    if log_sql:
        tools_log.log_db(sql, stack_level_increase=1)
    result = dao.execute_sql(sql, commit, aux_conn=aux_conn)
    lib_vars.session_vars['last_error'] = dao.last_error
    if not result:
        if log_error:
            tools_log.log_info(sql, stack_level_increase=1)
        if show_exception and not is_thread:
            tools_qt.manage_exception_db(lib_vars.session_vars['last_error'], sql, filepath=filepath)
        return False

    return True


def cancel_pid(pid):
    """ Cancel one process by pid """
    global dao  # noqa: F824
    return dao.cancel_pid(pid)


def execute_returning(sql, log_sql=False, log_error=False, commit=True, is_thread=False, show_exception=True):
    """ Execute SQL. Check its result in log tables, and show it to the user """

    global dao  # noqa: F824
    if log_sql:
        tools_log.log_db(sql, stack_level_increase=1)
    value = dao.execute_returning(sql, commit)
    lib_vars.session_vars['last_error'] = dao.last_error
    if not value:
        if log_error:
            tools_log.log_info(sql, stack_level_increase=1)
        if show_exception and not is_thread:
            tools_qt.manage_exception_db(lib_vars.session_vars['last_error'], sql)
        return False

    return value


def set_search_path(schema_name):
    """ Set parameter search_path for current QGIS project """

    global dao  # noqa: F824
    sql = f"SET search_path = {schema_name}, public;"
    execute_sql(sql)
    dao.set_search_path = sql


def check_function(function_name, schema_name=None, commit=True, aux_conn=None, is_thread=False):
    """ Check if @function_name exists in selected schema """

    if schema_name is None:
        schema_name = lib_vars.schema_name

    schema_name = schema_name.replace('"', '')
    sql = (f"SELECT routine_name "
           f"FROM information_schema.routines "
           f"WHERE lower(routine_schema) = '{schema_name}' "
           f"AND lower(routine_name) = '{function_name}'")
    row = get_row(sql, commit=commit, aux_conn=aux_conn, is_thread=is_thread)
    return row


def connect_to_database_credentials(credentials, conn_info=None, max_attempts=2):
    """ Connect to database with selected database @credentials """

    # Check if credential parameter 'service' is set
    if credentials.get('service'):
        logged, credentials_pgservice = connect_to_database_service(
            credentials['service'], credentials['sslmode'], conn_info
        )
        credentials['user'] = credentials_pgservice['user']
        credentials['password'] = credentials_pgservice['password']
        return logged, credentials

    attempt = 0
    logged = False
    while not logged and attempt <= max_attempts:
        attempt += 1
        if conn_info and attempt > 1:
            (success, credentials['user'], credentials['password']) = \
                QgsCredentials.instance().get(conn_info, credentials['user'], credentials['password'])
        logged = connect_to_database(credentials['host'], credentials['port'], credentials['db'],
                                     credentials['user'], credentials['password'], credentials['sslmode'])

    return logged, credentials


def _get_sslmode_from_settings(settings, sslmode_default):
    """Get SSL mode from QGIS settings"""
    sslmode_settings = settings.value('sslmode')
    try:
        sslmode_dict = {
            0: 'prefer', 1: 'disable', 3: 'require',
            'SslPrefer': 'prefer', 'SslDisable': 'disable', 'SslRequire': 'require', 'SslAllow': 'allow'
        }
        return sslmode_dict.get(sslmode_settings, sslmode_default)
    except ValueError:
        return sslmode_settings


def _get_credentials_from_layer(layer, sslmode_default):
    """Get database credentials from a QGIS layer"""
    credentials = tools_qgis.get_layer_source(layer)
    not_version = False

    # Handle SSL mode
    if not credentials['sslmode']:
        if credentials['service']:
            msg = "Getting {0} from .{1} file"
            msg_params = ("sslmode", "pg_service",)
            tools_log.log_info(msg, msg_params=msg_params)
            credentials_service = tools_os.manage_pg_service(credentials['service'])
            credentials['sslmode'] = credentials_service['sslmode'] if credentials_service['sslmode'] else sslmode_default  # noqa: E501
        else:
            settings = QSettings()
            settings.beginGroup("PostgreSQL/connections")
            if settings.value('selected'):
                default_connection = settings.value('selected')
                settings.endGroup()
                settings.beginGroup(f"PostgreSQL/connections/{default_connection}")
                credentials['sslmode'] = _get_sslmode_from_settings(settings, sslmode_default)
                settings.endGroup()

    lib_vars.schema_name = credentials['schema']
    return credentials, not_version


def _get_credentials_from_settings(sslmode_default):
    """Get database credentials from QGIS settings"""
    settings = QSettings()
    settings.beginGroup("PostgreSQL/connections")
    default_connection = settings.value('selected')
    settings.endGroup()

    if not default_connection:
        msg = "Error getting default connection (settings)"
        tools_log.log_warning(msg)
        lib_vars.session_vars['last_error'] = tools_qt.tr("Error getting default connection", "ui_message")
        return None, True

    settings.beginGroup(f"PostgreSQL/connections/{default_connection}")
    credentials = {
        'db': None, 'schema': None, 'table': None, 'service': None,
        'host': None, 'port': None, 'user': None, 'password': None, 'sslmode': None
    }

    credentials['host'] = settings.value('host') or 'localhost'
    credentials['port'] = settings.value('port')
    credentials['db'] = settings.value('database')
    credentials['user'] = settings.value('username')
    credentials['password'] = settings.value('password')
    credentials['service'] = settings.value('service')

    if credentials['service']:
        msg = "Getting {0} from .{1} file"
        msg_params = ("sslmode", "pg_service",)
        tools_log.log_info(msg, msg_params=msg_params)
        credentials_service = tools_os.manage_pg_service(credentials['service'])
        credentials['sslmode'] = credentials_service['sslmode'] if credentials_service['sslmode'] else sslmode_default
    else:
        credentials['sslmode'] = _get_sslmode_from_settings(settings, sslmode_default)

    settings.endGroup()
    return credentials, True


def get_layer_source_from_credentials(sslmode_default, layer_name='v_edit_node'):
    """Get database parameters from layer @layer_name or database connection settings
    sslmode_default should be (disable, allow, prefer, require, verify-ca, verify-full)"""

    global dao_db_credentials  # noqa: F824

    # Get layer and settings
    layer = tools_qgis.get_layer_by_tablename(layer_name)
    settings = QSettings()
    settings.beginGroup("PostgreSQL/connections")

    if layer is None and settings is None:
        msg = "Layer '{0}' is None and settings is None"
        msg_params = (layer_name,)
        tools_log.log_warning(msg, msg_params=msg_params)
        lib_vars.session_vars['last_error'] = f"Layer not found: '{layer_name}'"
        return None, False

    # Get credentials based on available source
    if layer:
        credentials, not_version = _get_credentials_from_layer(layer, sslmode_default)
    else:
        credentials, not_version = _get_credentials_from_settings(sslmode_default)

    if not credentials:
        return None, not_version

    # Connect to database
    if layer:
        conn_info = QgsDataSourceUri(layer.dataProvider().dataSourceUri()).connectionInfo()
        status, credentials = connect_to_database_credentials(credentials, conn_info)
        if not status:
            msg = "Error connecting to database (layer)"
            tools_log.log_warning(msg)
            lib_vars.session_vars['last_error'] = tools_qt.tr("Error connecting to database", "ui_message")
            return None, not_version
        QgsCredentials.instance().put(conn_info, credentials['user'], credentials['password'])
    else:
        status, credentials = connect_to_database_credentials(credentials, max_attempts=0)
        if not status:
            msg = "Error connecting to database (settings)"
            tools_log.log_warning(msg)
            lib_vars.session_vars['last_error'] = tools_qt.tr("Error connecting to database", "ui_message")
            return None, not_version

    dao_db_credentials = credentials
    return credentials, not_version


def get_uri(tablename=None, geom=None, schema_name=None):
    """ Set the component parts of a RDBMS data source URI
    :return: QgsDataSourceUri() with the connection established according to the parameters of the credentials.
    """

    global dao_db_credentials  # noqa: F824
    uri = QgsDataSourceUri()
    sslmode_default = QgsDataSourceUri.SslMode.SslPrefer
    sslmode_creds: str = dao_db_credentials['sslmode']
    try:
        sslmode_dict = {
            'prefer': QgsDataSourceUri.SslMode.SslPrefer,
            'disable': QgsDataSourceUri.SslMode.SslDisable,
            'require': QgsDataSourceUri.SslMode.SslRequire,
            'allow': QgsDataSourceUri.SslMode.SslAllow
        }
        sslmode = sslmode_dict.get(sslmode_creds, sslmode_default)
    except ValueError:
        sslmode = sslmode_default
    if dao_db_credentials['service']:
        uri.setConnection(dao_db_credentials['service'], None, None, '', sslmode)
    else:
        if tools_os.set_boolean(lib_vars.project_vars['store_credentials'], default=True):
            uri.setConnection(dao_db_credentials['host'], dao_db_credentials['port'],
                dao_db_credentials['db'], dao_db_credentials['user'], dao_db_credentials['password'],
                sslmode)
        else:
            uri.setConnection(dao_db_credentials['host'], dao_db_credentials['port'],
                              dao_db_credentials['db'], None, '', sslmode)
    if geom is not None and geom != 'None' and tablename is not None:
        geom_type = execute_returning(f"SELECT type FROM geometry_columns WHERE f_table_name = "
                                      f"'{tablename}' AND f_table_schema = '{schema_name}' LIMIT 1;")
        geom_type_map = {
            'POINT': QgsWkbTypes.Point,
            'LINESTRING': QgsWkbTypes.LineString,
            'POLYGON': QgsWkbTypes.Polygon,
            'MULTIPOINT': QgsWkbTypes.MultiPoint,
            'MULTILINESTRING': QgsWkbTypes.MultiLineString,
            'MULTIPOLYGON': QgsWkbTypes.MultiPolygon,
            'POINTZ': QgsWkbTypes.PointZ,
            'LINESTRINGZ': QgsWkbTypes.LineStringZ,
            'POLYGONZ': QgsWkbTypes.PolygonZ,
            'MULTIPOINTZ': QgsWkbTypes.MultiPointZ,
            'MULTILINESTRINGZ': QgsWkbTypes.MultiLineStringZ,
            'MULTIPOLYGONZ': QgsWkbTypes.MultiPolygonZ,
            'POINTM': QgsWkbTypes.PointM,
            'LINESTRINGM': QgsWkbTypes.LineStringM,
            'POLYGONM': QgsWkbTypes.PolygonM,
            'MULTIPOINTM': QgsWkbTypes.MultiPointM,
            'MULTILINESTRINGM': QgsWkbTypes.MultiLineStringM,
            'MULTIPOLYGONM': QgsWkbTypes.MultiPolygonM,
            'POINTZM': QgsWkbTypes.PointZM,
            'LINESTRINGZM': QgsWkbTypes.LineStringZM,
            'POLYGONZM': QgsWkbTypes.PolygonZM,
            'MULTIPOINTZM': QgsWkbTypes.MultiPointZM,
            'MULTILINESTRINGZM': QgsWkbTypes.MultiLineStringZM,
            'MULTIPOLYGONZM': QgsWkbTypes.MultiPolygonZM,
        }
        geom_key = geom_type[0].upper()
        wkb_type = geom_type_map.get(geom_key, QgsWkbTypes.Point)
        uri.setWkbType(wkb_type)
        return uri, True
    return uri, False

# region private functions


def _get_sql(sql, log_sql=False, params=None):
    """ Generate SQL with params. Useful for debugging """

    global dao  # noqa: F824
    if params:
        sql = dao.mogrify(sql, params)
    if log_sql:
        tools_log.log_db(sql, bold='b', stack_level_increase=2)

    return sql

# endregion
