# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QDialog

from qgis.utils import iface

from .settingsdialog import Ui_SettingsDialog


class SettingsDialog(QDialog, Ui_SettingsDialog):

    settingsChanged = pyqtSignal()
    colorChanged = pyqtSignal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.settings = settings

        self.resetting = False
        self.setWindowIcon(QIcon(":/plugins/multilayerselect/icons/icon.svg"))

        self.selectionColorButton.setDefaultColor(QColor("yellow"))
        self.selectionColorButton.setColor(iface.mapCanvas().selectionColor())

        self.activeLayerCheckBox.setChecked(
            self.settings.value("set_active_layer", True, bool)
        )
        self.showSettingsCheckBox.setChecked(
            self.settings.value("show_settings", True, bool)
        )
        self.replaceActionsCheckBox.setChecked(
            self.settings.value("replace_actions", False, bool)
        )

        # Connect signals
        self.selectionColorButton.colorChanged.connect(self.on_color_changed)
        self.activeLayerCheckBox.toggled.connect(self.on_active_layer_changed)
        self.showSettingsCheckBox.toggled.connect(self.on_show_settings_changed)
        self.replaceActionsCheckBox.toggled.connect(self.on_replace_actions_changed)

    def on_color_changed(self, color):
        iface.mapCanvas().setSelectionColor(color)
        if not self.resetting:
            self.colorChanged.emit()

    def on_active_layer_changed(self, checked):
        self.settings.setValue("set_active_layer", checked)
        if not self.resetting:
            self.settingsChanged.emit()

    def on_show_settings_changed(self, checked):
        self.settings.setValue("show_settings", checked)
        if not self.resetting:
            self.settingsChanged.emit()

    def on_replace_actions_changed(self, checked):
        self.settings.setValue("replace_actions", checked)
        if not self.resetting:
            self.settingsChanged.emit()
