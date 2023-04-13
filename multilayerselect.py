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

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtWidgets import (
    QAction,
    QMessageBox,
    QWidget,
    QToolBar,
    QToolButton,
)

from qgis.core import QgsProject, QgsVectorLayer

from .settingsdialogimpl import SettingsDialog
from .icon_utils import (
    create_icon,
    select_all_icon,
    invert_selection_icon,
    expression_select_icon,
)
from .maptools import (
    MultiSelectionAreaTool,
    MultiSelectionPolygonTool,
    MultiSelectionRadiusTool,
    MultiSelectionFreehandTool,
    update_status_message,
)

from .utils import vector_layers

from .multiselectionexpressionbuilder import MultiLayerSelectionExpressionBuilder

from .resources import *  # noqa


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
        locale_path = os.path.join(self.plugin_dir, "i18n", "MultiLayerSelect_{}.qm".format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Init settings
        self.settings = QSettings()
        self.settings.beginGroup("plugins/multilayerselect")

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """

        return QCoreApplication.translate("MultiLayerSelect", message)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        # Create settings dialog
        self.settings_dialog = SettingsDialog(self.settings, self.iface.mainWindow())
        self.expression_dialog = None

        try:
            QgsProject.instance().selectionColorChanged.connect(self.on_color_changed)
            QgsProject.instance().selectionColorChanged.connect(self.settings_dialog.on_project_color_changed)
        except AttributeError:  # QGIS < 3.10
            self.settings_dialog.colorChanged.connect(self.on_color_changed)
            QgsProject.instance().readProject.connect(self.settings_dialog.on_project_color_changed)

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

            action.triggered.connect(partial(on_select_tool, select_action.tool, action))
            self.selection_tool_button.addAction(action)
            if not self.selection_tool_button.defaultAction():
                self.selection_tool_button.setDefaultAction(action)
            self.select_actions.append(action)

        self.toolbar.addWidget(self.selection_tool_button)

        self.select_all_action = QAction(
            self.tr("Select all features from all layers"),
        )
        self.select_all_action.setToolTip("<b>{}</b>".format(self.select_all_action.text()))
        self.select_all_action.setObjectName("actionMultiSelectAll")
        self.select_all_action.triggered.connect(self.select_all)
        self.advanced_selection_tool_button.addAction(self.select_all_action)
        self.advanced_selection_tool_button.setDefaultAction(self.select_all_action)

        self.invert_all_action = QAction(
            self.tr("Invert selection for all layers"),
        )
        self.invert_all_action.setToolTip("<b>{}</b>".format(self.invert_all_action.text()))
        self.invert_all_action.setObjectName("actionMultiSelectInvert")
        self.invert_all_action.triggered.connect(self.invert_all)
        self.advanced_selection_tool_button.addAction(self.invert_all_action)

        self.select_by_expr_action = QAction(
            QIcon(":/images/themes/default/mIconExpressionSelect.svg"),
            self.tr("Select Features by Expression..."),
        )
        self.select_by_expr_action.setToolTip("<b>{}</b>".format(self.select_by_expr_action.text()))
        self.select_by_expr_action.setObjectName("actionMultiSelectExpr")
        self.select_by_expr_action.triggered.connect(self.select_by_expression)
        self.advanced_selection_tool_button.addAction(self.select_by_expr_action)

        self.toolbar.addWidget(self.advanced_selection_tool_button)

        self.deselect_all_action = QAction(self.tr("Deselect features from all layers"))
        self.deselect_all_action.setToolTip("<b>{}</b>".format(self.deselect_all_action.text()))
        self.deselect_all_action.setObjectName("actionDeselectAll")
        self.deselect_all_action.triggered.connect(self.deselect_all)
        self.toolbar.addAction(self.deselect_all_action)

        self.toolbar.addAction(self.settings_action)

        self.iface.mainWindow().addToolBar(self.toolbar)

        # Embedded actions
        self.embedded_selection_tool_button_action = None
        self.embedded_selection_tool_button = None
        self.embedded_advanced_tool_button_action = None
        self.embedded_advanced_tool_button = None

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

        try:
            QgsProject.instance().selectionColorChanged.disconnect(self.on_color_changed)
            QgsProject.instance().selectionColorChanged.disconnect(self.settings_dialog.on_project_color_changed)

        except AttributeError:  # QGIS < 3.10
            pass

    def show_about(self):
        """Show the about dialog"""

        # Used to display plugin icon in the about message box
        bogus = QWidget(self.iface.mainWindow())
        bogus.setWindowIcon(QIcon(":/plugins/multilayerselect/icons/icon.svg"))

        cfg = configparser.ConfigParser()
        cfg.read(os.path.join(os.path.dirname(__file__), "metadata.txt"))
        version = cfg.get("general", "version")
        homepage = cfg.get("general", "homepage")
        tracker = cfg.get("general", "tracker")
        repository = cfg.get("general", "repository")

        QMessageBox.about(
            bogus,
            self.tr("About Multilayer Select"),
            "<b>Version</b> {3}<br><br>"
            "<b>{4}</b> : <a href={0}>GitHub</a><br>"
            "<b>{5}</b> : <a href={1}>GitHub</a><br>"
            "<b>{6}</b> : <a href={2}>GitHub Pages</a>".format(
                repository,
                tracker,
                homepage,
                version,
                self.tr("Source code"),
                self.tr("Report issues"),
                self.tr("Documentation"),
            ),
        )

        bogus.deleteLater()

    def show_settings(self):
        """Show the settings dialog"""

        geometry = self.settings_dialog.geometry()

        # The first time the dialog is shown (y=0), explicitely set its geometry
        # which allow to restore the geometry on subsequent calls
        if geometry.y() == 0:
            self.settings_dialog.show()
            self.settings_dialog.raise_()
            self.settings_dialog.setGeometry(self.settings_dialog.geometry())
            return

        self.settings_dialog.show()
        self.settings_dialog.raise_()

    def on_color_changed(self):
        """Called when the selection color has changed. Replace every icon"""
        color = self.iface.mapCanvas().selectionColor()
        color = QColor.fromHsv(
            int(color.hue()),
            int(color.saturation() * 0.9),
            int(color.value() * 0.95),
            int(color.alpha()),
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

        icon = expression_select_icon(color)
        self.select_by_expr_action.setIcon(icon)

    def on_settings_changed(self):
        """Called when any setting has changed"""
        if self.settings.value("show_settings", True, bool):
            self.toolbar.addAction(self.settings_action)
        else:
            self.toolbar.removeAction(self.settings_action)

        self.replace_default_action(self.settings.value("replace_actions", False, bool))

    def deselect_all(self):
        """Deselect every feature"""
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer):
                layer.removeSelection()
        update_status_message()

    def select_all(self):
        """Select all the features from every vector layer"""
        for layer in vector_layers():
            layer.selectAll()
        self.advanced_selection_tool_button.setDefaultAction(self.select_all_action)

        if self.embedded_advanced_tool_button:
            self.embedded_advanced_tool_button.setDefaultAction(self.select_all_action)

        update_status_message()

    def invert_all(self):
        """Invert the selection of every vector layer"""
        for layer in vector_layers():
            layer.invertSelection()
        self.advanced_selection_tool_button.setDefaultAction(self.invert_all_action)

        if self.embedded_advanced_tool_button:
            self.embedded_advanced_tool_button.setDefaultAction(self.invert_all_action)
        update_status_message()

    def select_by_expression(self):
        """Create and open the Expression builder dialog"""

        if self.expression_dialog:
            self.expression_dialog.deleteLater()
        self.expression_dialog = MultiLayerSelectionExpressionBuilder()
        self.expression_dialog.show()

        self.advanced_selection_tool_button.setDefaultAction(self.select_by_expr_action)

        if self.embedded_advanced_tool_button:
            self.embedded_advanced_tool_button.setDefaultAction(self.select_by_expr_action)
        update_status_message()

    def replace_default_action(self, value):
        """Replace the default QGIS selection action with the multilayer ones

        Args:
            value (bool): If true, replace the actions, else put the multi actions
                inside their own toolbar
        """

        toolbar = self.iface.attributesToolBar()
        main_window = self.iface.mainWindow()
        main_window.findChild(QAction, "ActionSelect").setVisible(not value)
        main_window.findChild(QAction, "ActionSelection").setVisible(not value)
        main_window.findChild(QAction, "mActionDeselectAll").setVisible(not value)

        actiontable = main_window.findChild(QAction, "mActionOpenTable")
        actionform = main_window.findChild(QAction, "mActionSelectByForm")

        # Remove the multi layer tool buttons from the QGIS attribute toolbar
        toolbar.removeAction(self.embedded_selection_tool_button_action)
        toolbar.removeAction(self.embedded_advanced_tool_button_action)

        if value:
            # Create the QToolButtons that will be added to the default toolbar
            self.embedded_selection_tool_button = QToolButton()
            self.embedded_selection_tool_button.setPopupMode(QToolButton.MenuButtonPopup)

            # Add selection tools action to the button (Rect, Polygon, Radius, Freehand)
            self.embedded_selection_tool_button.addActions(self.select_actions)
            self.embedded_selection_tool_button.setDefaultAction(self.select_actions[0])

            self.embedded_advanced_tool_button = QToolButton()
            self.embedded_advanced_tool_button.setPopupMode(QToolButton.MenuButtonPopup)

            # Add Invert, Select All, Select from value and Select from expressions
            self.embedded_advanced_tool_button.addAction(self.select_all_action)
            self.embedded_advanced_tool_button.setDefaultAction(self.select_all_action)
            self.embedded_advanced_tool_button.addAction(self.invert_all_action)
            self.embedded_advanced_tool_button.addAction(self.select_by_expr_action)
            self.embedded_advanced_tool_button.addAction(actionform)

            self.embedded_selection_tool_button_action = toolbar.insertWidget(
                actiontable, self.embedded_selection_tool_button
            )
            self.embedded_advanced_tool_button_action = toolbar.insertWidget(
                actiontable, self.embedded_advanced_tool_button
            )

            # Add the deselect all action
            toolbar.insertAction(actiontable, self.deselect_all_action)

            # If the settigns is enabled add the show settings action
            if self.settings.value("show_settings", True, bool):
                toolbar.insertAction(actiontable, self.settings_action)
            else:
                toolbar.removeAction(self.settings_action)
            self.toolbar.hide()

        else:
            # Remove the multi actions from the default toolbar, and show
            # the custom toolbar
            self.embedded_selection_tool_button = None
            self.embedded_advanced_tool_button = None
            toolbar.removeAction(self.deselect_all_action)
            toolbar.removeAction(self.settings_action)
            self.toolbar.show()


class SelectAction:
    """Structure used to define a selection action"""

    def __init__(self, text, **kwargs):
        self.text = text
        self.tooltip = "<b>{}</b>".format(text)
        self.icon = ":/plugins/multilayerselect/icons/selectRectangle.svg"
        self.objectname = ""
        self.tool = None
        self.__dict__.update(kwargs)
