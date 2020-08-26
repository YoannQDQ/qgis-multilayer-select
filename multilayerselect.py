# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Multilayer Select
 Multilayer selection tools

                              -------------------
        begin                : 2020-09-01
        git sha              : $Format:%H$
        copyright            : (C) 2020 Yoann Quenach de Quivillic
        email                : yoann.quenach@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os
import configparser
from functools import partial

from PyQt5.QtCore import QSettings, QTranslator, QCoreApplication
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import (
    QAction,
    QMessageBox,
    QWidget,
    QToolBar,
    QToolButton,
)

from .settingsdialogimpl import SettingsDialog

from .icon_utils import create_icon, select_all_icon, invert_selection_icon

from .maptools import (
    MultiSelectionAreaTool,
    MultiSelectionPolygonTool,
    MultiSelectionRadiusTool,
    MultiSelectionFreehandTool,
)

from qgis.core import QgsProject, QgsVectorLayer

from .resources import *


class SelectAction:
    def __init__(self, text, **kwargs):
        self.text = text
        self.tooltip = f"<b>{text}</b>"
        self.icon = ":/plugins/multilayerselect/icons/selectRectangle.svg"
        self.objectname = ""
        self.tool = None
        self.__dict__.update(kwargs)


class MultiLayerSelect:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(
            self.plugin_dir, "i18n", "MultiLayerSelect_{}.qm".format(locale)
        )

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Init settings
        self.settings = QSettings()
        self.settings.beginGroup("plugins/multilayerselect")

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate("MultiLayerSelect", message)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        # Create settings dialog
        self.settings_dialog = SettingsDialog(self.settings, self.iface.mainWindow())
        self.settings_dialog.colorChanged.connect(self.on_color_changed)
        self.settings_dialog.settingsChanged.connect(self.on_settings_changed)

        self.toolbar = QToolBar("Multilayer Select", self.iface.mainWindow())
        self.toolbar.setObjectName("MultiSelectToolbar")

        self.about_action = QAction(
            QIcon(":/plugins/multilayerselect/icons/about.svg"),
            self.tr("About"),
            parent=self.iface.mainWindow(),
        )
        self.about_action.triggered.connect(self.show_about)

        self.settings_action = QAction(
            QIcon(":/images/themes/default/console/iconSettingsConsole.svg"),
            self.tr("Settings"),
            parent=self.iface.mainWindow(),
        )
        self.settings_action.setObjectName("actionMultiLayerSelectSettings")
        self.settings_action.setToolTip(self.tr("<b>Multilayer Select Settings</b>"))

        self.settings_action.triggered.connect(self.show_settings)

        self.plugin_menu = self.iface.pluginMenu().addMenu(
            QIcon(":/plugins/multilayerselect/icons/icon.svg"), "Multilayer Select"
        )
        self.plugin_menu.addAction(self.about_action)
        self.plugin_menu.addAction(self.settings_action)

        self.selection_tool_button = QToolButton(self.toolbar)
        self.selection_tool_button.setPopupMode(QToolButton.MenuButtonPopup)
        self.selection_tool_button.setObjectName("selectionToolButton")

        self.advanced_selection_tool_button = QToolButton(self.toolbar)
        self.advanced_selection_tool_button.setPopupMode(QToolButton.MenuButtonPopup)
        self.advanced_selection_tool_button.setObjectName("advancedSelectionToolButton")

        self.select_rect_tool = MultiSelectionAreaTool(self.iface.mapCanvas())
        self.select_polygon_tool = MultiSelectionPolygonTool(self.iface.mapCanvas())
        self.select_freehand_tool = MultiSelectionFreehandTool(self.iface.mapCanvas())
        self.select_radius_tool = MultiSelectionRadiusTool(self.iface.mapCanvas())

        self.actions_settings = [
            SelectAction(
                text=self.tr("Select Features"),
                tooltip=self.tr("<b>Select Features by area or single click</b>"),
                icon=":/plugins/multilayerselect/icons/selectRectangle.svg",
                objectname="actionMultiSelectByRectangle",
                tool=self.select_rect_tool,
            ),
            SelectAction(
                text=self.tr("Select Features by Polygon"),
                icon=":/plugins/multilayerselect/icons/selectPolygon.svg",
                objectname="actionMultiSelectByPolygon",
                tool=self.select_polygon_tool,
            ),
            SelectAction(
                text=self.tr("Select Features by Freehand"),
                icon=":/plugins/multilayerselect/icons/selectFreehand.svg",
                objectname="actionMultiSelectByFreehand",
                tool=self.select_freehand_tool,
            ),
            SelectAction(
                text=self.tr("Select Features by Radius"),
                icon=":/plugins/multilayerselect/icons/selectRadius.svg",
                objectname="actionMultiSelectByRadius",
                tool=self.select_radius_tool,
            ),
        ]

        def on_select_tool(tool, action):
            self.selection_tool_button.setDefaultAction(action)
            if self.embedded_selection_tool_button:
                self.embedded_selection_tool_button.setDefaultAction(action)
            self.iface.mapCanvas().setMapTool(tool)

        self.select_actions = []

        for select_action in self.actions_settings:
            action = QAction(select_action.text)
            action.setToolTip(select_action.tooltip)
            action.setObjectName(select_action.objectname)
            action.setCheckable(True)
            select_action.tool.setAction(action)

            action.triggered.connect(
                partial(on_select_tool, select_action.tool, action)
            )
            self.selection_tool_button.addAction(action)
            if not self.selection_tool_button.defaultAction():
                self.selection_tool_button.setDefaultAction(action)
            self.select_actions.append(action)

        self.toolbar.addWidget(self.selection_tool_button)

        self.select_all_action = QAction(
            self.tr("Select all features from all layers"),
        )
        self.select_all_action.setToolTip(f"<b>{self.select_all_action.text()}</b>")
        self.select_all_action.setObjectName("actionMultiSelectAll")
        self.select_all_action.triggered.connect(self.select_all)
        self.advanced_selection_tool_button.addAction(self.select_all_action)
        self.advanced_selection_tool_button.setDefaultAction(self.select_all_action)

        self.invert_all_action = QAction(self.tr("Invert selection for all layers"),)
        self.invert_all_action.setToolTip(f"<b>{self.invert_all_action.text()}</b>")
        self.invert_all_action.setObjectName("actionMultiSelectInvert")
        self.invert_all_action.triggered.connect(self.invert_all)
        self.advanced_selection_tool_button.addAction(self.invert_all_action)
        self.toolbar.addWidget(self.advanced_selection_tool_button)

        self.deselect_all_action = QAction(self.tr("Deselect features from all layers"))
        self.deselect_all_action.setToolTip(f"<b>{self.deselect_all_action.text()}</b>")
        self.deselect_all_action.setObjectName("actionDeselectAll")
        self.deselect_all_action.triggered.connect(self.deselect_all)
        self.toolbar.addAction(self.deselect_all_action)

        self.toolbar.addAction(self.settings_action)

        self.iface.mainWindow().addToolBar(self.toolbar)

        self.on_color_changed()
        self.on_settings_changed()

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        # Delete Settings dialog
        self.settings_dialog.deleteLater()

        # Remove menu from plugins menu
        self.iface.pluginMenu().removeAction(self.plugin_menu.menuAction())

        self.select_freehand_tool.deleteLater()
        self.select_polygon_tool.deleteLater()
        self.select_radius_tool.deleteLater()
        self.select_rect_tool.deleteLater()

        self.iface.mainWindow().removeToolBar(self.toolbar)
        self.toolbar.deleteLater()

        self.replace_default_action(False)

    def show_about(self):

        # Used to display plugin icon in the about message box
        bogus = QWidget(self.iface.mainWindow())
        bogus.setWindowIcon(QIcon(":/plugins/multilayerselect/icons/icon.svg"))

        cfg = configparser.ConfigParser()
        cfg.read(os.path.join(os.path.dirname(__file__), "metadata.txt"))
        version = cfg.get("general", "version")

        QMessageBox.about(
            bogus,
            self.tr("About Multilayer Select"),
            "<b>Version</b> {0}<br><br>"
            "<b>{1}</b> : <a href=https://github.com/YoannQDQ/qgis-multilayer-select>GitHub</a><br>"
            "<b>{2}</b> : <a href=https://github.com/YoannQDQ/qgis-multilayer-select/issues>GitHub</a><br>"
            "<b>{3}</b> : <a href=https://github.com/YoannQDQ/qgis-multilayer-select#multilayer-select-qgis-plugin>GitHub</a>".format(
                version,
                self.tr("Source code"),
                self.tr("Report issues"),
                self.tr("Documentation"),
            ),
        )

        bogus.deleteLater()

    def show_settings(self):

        self.settings_dialog.show()
        self.settings_dialog.raise_()

    def on_color_changed(self):
        color = self.iface.mapCanvas().selectionColor()
        color = QColor.fromHsv(
            color.hue(), color.saturation() * 0.9, color.value() * 0.95, color.alpha()
        )
        for i in range(len(self.select_actions)):
            path = self.actions_settings[i].icon
            icon = create_icon(path, color)
            self.select_actions[i].setIcon(icon)

        icon = create_icon(":/plugins/multilayerselect/icons/deselectAll.svg", color)
        self.deselect_all_action.setIcon(icon)

        icon = select_all_icon(color)
        self.select_all_action.setIcon(icon)

        icon = invert_selection_icon(color)
        self.invert_all_action.setIcon(icon)

    def on_settings_changed(self):
        if self.settings.value("show_settings", True, bool):
            self.toolbar.addAction(self.settings_action)
        else:
            self.toolbar.removeAction(self.settings_action)

        self.replace_default_action(self.settings.value("replace_actions", False, bool))

    def deselect_all(self):
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer):
                layer.removeSelection()

    def select_all(self):
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer):
                layer.selectAll()
        self.advanced_selection_tool_button.setDefaultAction(self.select_all_action)

        if self.embedded_advanced_tool_button:
            self.embedded_advanced_tool_button.setDefaultAction(self.select_all_action)

    def invert_all(self):
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer):
                layer.invertSelection()
        self.advanced_selection_tool_button.setDefaultAction(self.invert_all_action)

        if self.embedded_advanced_tool_button:
            self.embedded_advanced_tool_button.setDefaultAction(self.invert_all_action)

    def replace_default_action(self, value):

        toolbar = self.iface.attributesToolBar()
        mainWindow = self.iface.mainWindow()
        mainWindow.findChild(QAction, "ActionSelect").setVisible(not value)
        mainWindow.findChild(QAction, "ActionSelection").setVisible(not value)
        mainWindow.findChild(QAction, "mActionDeselectAll").setVisible(not value)

        actiontable = mainWindow.findChild(QAction, "mActionOpenTable")
        actionform = mainWindow.findChild(QAction, "mActionSelectByForm")
        actionexpression = mainWindow.findChild(QAction, "mActionSelectByExpression")

        try:
            toolbar.removeAction(self.temp_action)
            toolbar.removeAction(self.temp_action2)
        except:
            pass

        if value:

            self.embedded_selection_tool_button = QToolButton()
            self.embedded_selection_tool_button.setPopupMode(
                QToolButton.MenuButtonPopup
            )

            self.embedded_selection_tool_button.addActions(self.select_actions)
            self.embedded_selection_tool_button.setDefaultAction(self.select_actions[0])

            self.embedded_advanced_tool_button = QToolButton()
            self.embedded_advanced_tool_button.setPopupMode(QToolButton.MenuButtonPopup)

            self.embedded_advanced_tool_button.addAction(self.select_all_action)
            self.embedded_advanced_tool_button.setDefaultAction(self.select_all_action)
            self.embedded_advanced_tool_button.addAction(self.invert_all_action)
            self.embedded_advanced_tool_button.addAction(actionform)
            self.embedded_advanced_tool_button.addAction(actionexpression)

            self.temp_action = toolbar.insertWidget(
                actiontable, self.embedded_selection_tool_button
            )
            self.temp_action2 = toolbar.insertWidget(
                actiontable, self.embedded_advanced_tool_button
            )

            toolbar.insertAction(actiontable, self.deselect_all_action)
            if self.settings.value("show_settings", True, bool):
                toolbar.insertAction(actiontable, self.settings_action)
            else:
                toolbar.removeAction(self.settings_action)
            self.toolbar.hide()
        else:
            self.embedded_selection_tool_button = None
            self.embedded_advanced_tool_button = None
            toolbar.removeAction(self.deselect_all_action)
            toolbar.removeAction(self.settings_action)
            self.toolbar.show()

