# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSignal, QSettings
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QDialog

from qgis.utils import iface
from qgis.core import QgsProject

from .settingsdialog import Ui_SettingsDialog


class SettingsDialog(QDialog, Ui_SettingsDialog):

    settingsChanged = pyqtSignal()
    colorChanged = pyqtSignal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.settings = settings

        self.setWindowIcon(QIcon(":/plugins/multilayerselect/icons/icon.svg"))

        qgis_settings = QSettings()
        red = qgis_settings.value("qgis/default_selection_color_red", 255, int)
        green = qgis_settings.value("qgis/default_selection_color_green", 255, int)
        blue = qgis_settings.value("qgis/default_selection_color_blue", 0, int)
        alpha = qgis_settings.value("qgis/default_selection_color_alpha", 255, int)

        self.selectionColorButton.setDefaultColor(
            QColor.fromRgb(red, green, blue, alpha)
        )
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

    def on_project_color_changed(self):
        try:
            self.selectionColorButton.setColor(QgsProject.instance().selectionColor())
        except AttributeError:  # QGIS < 3.10
            self.selectionColorButton.setColor(iface.mapCanvas().selectionColor())

    def on_color_changed(self, color: QColor):
        try:
            QgsProject.instance().setSelectionColor(color)
            QgsProject.instance().setDirty()
        except AttributeError:  # QGIS < 3.10
            iface.mapCanvas().setSelectionColor(color)
            QgsProject.instance().writeEntry(
                "Gui", "SelectionColorRedPart", color.red()
            )
            QgsProject.instance().writeEntry(
                "Gui", "SelectionColorBluePart", color.blue()
            )
            QgsProject.instance().writeEntry(
                "Gui", "SelectionColorGreenPart", color.green()
            )
            QgsProject.instance().writeEntry(
                "Gui", "SelectionColorAlphaPart", color.alpha()
            )

            self.colorChanged.emit()

    def on_active_layer_changed(self, checked):
        self.settings.setValue("set_active_layer", checked)
        self.settingsChanged.emit()

    def on_show_settings_changed(self, checked):
        self.settings.setValue("show_settings", checked)
        self.settingsChanged.emit()

    def on_replace_actions_changed(self, checked):
        self.settings.setValue("replace_actions", checked)
        self.settingsChanged.emit()
