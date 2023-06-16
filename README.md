# lib
This repository eases the development of QGIS python plugins by providing functions that bridge the gap between your plugin code and the PyQt, QGIS &amp; psycopg2 modules.

## File structure &amp; summary
```
📦lib
 ┣ 📂ui
 ┃ ┣ 📜__init__.py
 ┃ ┣ 📜dialog.py => Basic class that inherits QDialog
 ┃ ┣ 📜dialog_text.ui => Qt dialog with a text box
 ┃ ┗ 📜ui_manager.py => Loads the dialog_text.ui into a python class
 ┣ 📜__init__.py
 ┣ 📜lib_vars.py => Variables used by the different tools
 ┣ 📜tools_db.py => Methods to interact with a PostgreSQL database
 ┣ 📜tools_log.py => Methods to interact with QGIS Log Messages Panel
 ┣ 📜tools_os.py => Methods to interact with various system things
 ┣ 📜tools_pgdao.py => DAO for PostgreSQL database
 ┣ 📜tools_qgis.py => Methods to interact with QGIS
 ┗ 📜tools_qt.py => Methods to interact with PyQt
```

## Use
You can add this module in your plugin by running this command:

    git submodule add https://github.com/bgeo-gis/lib.git


This should've placed it in the root folder of your plugin like so:
```
📂amazing_plugin
 ┣ 📂config
 ┣ 📂core
 ┣ 📦lib
 ┣ 📜__init__.py
 ┣ 📜main.py
 ┗ 📜metadata.txt
```

## Technical details
A lot of functions use common variable between the diferent tools. They are stored in the file `lib_vars.py`. Your plugin can use these variables by simply importing `lib_vars`.
