"""
This file is part of Giswater
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-

schema_name = None                      # Schema name retrieved from QGIS project connection with PostgreSql
qgis_db_credentials = None              # Instance of class QSqlDatabase (QPSQL) used to manage QTableView widgets
last_db_credentials = None              # Last DB credentials used for QSqlDatabase connection (is used for resetting it)
plugin_name = None                      # Plugin name
plugin_dir = None                       # Plugin folder path
user_folder_dir = None                  # User folder path
logger = None                           # Instance of class GwLogger. Found in "/lib/tools_log.py"
project_vars = {}                       # Project variables from QgsProject related to Giswater
project_vars['info_type'] = None        # gwInfoType
project_vars['add_schema'] = None       # gwAddSchema
project_vars['main_schema'] = None      # gwMainSchema
project_vars['project_role'] = None     # gwProjectRole
project_vars['project_type'] = None     # gwProjectType
project_vars['store_credentials'] = None  # gwStoreCredentials
data_epsg = None                        # SRID retrieved from QGIS project layer "v_edit_node"
project_epsg = None                     # EPSG of QGIS project

# region Dynamic Variables (variables may change value during user's session)
session_vars = {}
session_vars['last_error'] = None          # An instance of the last database runtime error
session_vars['last_error_msg'] = None      # An instance of the last database runtime error message used in threads
session_vars['threads'] = []               # An instance of the different threads for the execution of the Giswater functionalities (type:list)
session_vars['dialog_docker'] = None       # An instance of GwDocker from "/core/ui/docker.py" which is used to mount a docker form
session_vars['info_docker'] = None         # An instance of current status of the info docker form configured by user. Can be True or False
session_vars['docker_type'] = None         # An instance of current status of the docker form configured by user. Can be configured "qgis_info_docker" and "qgis_form_docker"
session_vars['current_selections'] = None  # An instance of the current selections docker.
session_vars['logged_status'] = None       # An instance of connection status. Can be True or False
session_vars['last_focus'] = None          # An instance of the last focused dialog's tag
# endregion

# region global user variables (values are initialized on load project without changes during session)
user_level = {                          # An instance used to know user level and user level configuration
    'level': None,                      # initial=1, normal=2, expert=3
    'showquestion': None,               # Used for show help (default config show for level 1 and 2)
    'showsnapmessage': None,            # Used to indicate to the user that they can snapping
    'showselectmessage': None,          # Used to indicate to the user that they can select
    'showadminadvanced': None,          # Manage advanced tab, fields manager tab and sample dev radio button from admin
}
date_format = None                      # Display format of the dates allowed in the forms: dd/MM/yyyy or dd-MM-yyyy or yyyy/MM/dd or yyyy-MM-dd
# endregion
