import os
import sys
from unittest.mock import MagicMock


# Add the plugin directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Mock Qt classes
class MockQDialog:
    def __init__(self, *args, **kwargs):
        pass


class MockQWidget:
    def __init__(self, *args, **kwargs):
        pass


class MockQMainWindow:
    def __init__(self, *args, **kwargs):
        pass


class MockQMessageBox:
    def __init__(self, *args, **kwargs):
        pass


class MockQFileDialog:
    def __init__(self, *args, **kwargs):
        pass


# Mock Dialog class
class Dialog(MockQDialog):
    def __init__(self, *args, **kwargs):
        super().__init__()


# Mock FORM_CLASS
class FormClass(MockQDialog):
    def __init__(self, *args, **kwargs):
        super().__init__()


# Mock ShowInfoUi class
class ShowInfoUi(Dialog, FormClass):
    def __init__(self, *args, **kwargs):
        super().__init__()


# Set up mocks before any imports
def setup_qgis_mocks():
    """Setup all QGIS-related mocks"""
    # Mock QGIS imports
    sys.modules['qgis'] = MagicMock()
    sys.modules['qgis.PyQt'] = MagicMock()
    sys.modules['qgis.PyQt.QtCore'] = MagicMock()
    sys.modules['qgis.PyQt.QtWidgets'] = MagicMock()
    sys.modules['qgis.PyQt.QtGui'] = MagicMock()
    sys.modules['qgis.PyQt.QtSql'] = MagicMock()
    sys.modules['qgis.core'] = MagicMock()
    sys.modules['qgis.core.QgsMessageLog'] = MagicMock()
    sys.modules['qgis.gui'] = MagicMock()
    sys.modules['qgis.utils'] = MagicMock()
    sys.modules['qgis.PyQt.sip'] = MagicMock()
    sys.modules['qgis.PyQt.sip'].isdeleted = MagicMock(return_value=False)
    sys.modules['console'] = MagicMock()

    # Set up the mocks
    sys.modules['qgis.PyQt.QtWidgets'].QDialog = MockQDialog
    sys.modules['qgis.PyQt.QtWidgets'].QWidget = MockQWidget
    sys.modules['qgis.PyQt.QtWidgets'].QMainWindow = MockQMainWindow
    sys.modules['qgis.PyQt.QtWidgets'].QMessageBox = MockQMessageBox
    sys.modules['qgis.PyQt.QtWidgets'].QFileDialog = MockQFileDialog

    # Create and mock the UI manager module
    ui_manager_module = type('Module', (), {})()
    ui_manager_module.Dialog = Dialog
    ui_manager_module.FORM_CLASS = FormClass
    ui_manager_module.ShowInfoUi = ShowInfoUi
    sys.modules['libs.ui.ui_manager'] = ui_manager_module


# Call setup_qgis_mocks immediately
setup_qgis_mocks()
