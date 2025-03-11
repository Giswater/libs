"""
This file is part of Giswater
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-
import os
from warnings import warn

from qgis.PyQt import uic

from .dialog import Dialog


def get_ui_class(ui_file_name):
    """ Get UI Python class from @ui_file_name """

    # Folder that contains UI files
    ui_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ui_file_name))
    return uic.loadUiType(ui_file_path)[0]


FORM_CLASS = get_ui_class('show_info.ui')
class ShowInfoUi(Dialog, FORM_CLASS):
    pass

FORM_CLASS = get_ui_class('show_info.ui')
class DialogTextUi(Dialog, FORM_CLASS):
    warn('This class is deprecated, use ShowInfoUi instead.', DeprecationWarning, stacklevel=2)
    def __init__(self, icon=None):
        super().__init__(icon)
        warn('This class is deprecated, use ShowInfoUi instead.', DeprecationWarning, stacklevel=2)


