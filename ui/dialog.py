"""
This file is part of Giswater
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QDialog


class Dialog(QDialog):

    def __init__(self, icon=None):

        super().__init__()
        self.setupUi(self)

        if icon:
            self.setWindowIcon(icon)
