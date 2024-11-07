""" MultiLayer Select Settings Dialog
Allow to define:
 - The selection color used for selected feature, icons and rubberbands
 - Whether the plugin actions replace the default ones or not
 - Whether the settings action (which launch this dialog) is available in the toolbar
 - Whether selecting a feature changes the active layer
"""

from collections import Counter

from qgis.core import QgsMapLayerModel, QgsMapLayerProxyModel, QgsProject
from qgis.PyQt.QtCore import QSettings, Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor, QIcon
from qgis.PyQt.QtWidgets import QDialog
from qgis.utils import iface

from .settingsdialog import Ui_SettingsDialog
from .utils import icon_from_layer


class LayerModel(QgsMapLayerProxyModel):
    """Checkable Layer Model to include / exclude vector layers from the multilayer
    selection tools"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFilters(QgsMapLayerProxyModel.VectorLayer)

    def name_list(self):
        """Return the list of vector layer names"""
        names = []
        for i in range(self.rowCount()):
            names.append(super().data(self.index(i, 0)))

        return names

    def non_unique_names(self):
        """Return the list of non-unique vector layer names"""
        return [k for k, v in Counter(self.name_list()).items() if v > 1]

    def include_all(self):
        """Include all layers in the multiselection tools (default behavior)
        Remove the custom property from every layers"""
        for layer in QgsProject.instance().mapLayers().values():
            layer.removeCustomProperty("plugins/multilayerselect/excluded")
        self.dataChanged.emit(
            self.index(0, 0), self.index(self.rowCount(), 0), [Qt.CheckStateRole]
        )

    def exlude_all(self):
        """Exclude all layers from the multiselection tools
        This is done by addinf a custom property on the layers"""
        for layer in QgsProject.instance().mapLayers().values():
            layer.setCustomProperty("plugins/multilayerselect/excluded", True)
        self.dataChanged.emit(
            self.index(0, 0), self.index(self.rowCount(), 0), [Qt.CheckStateRole]
        )

    def flags(self, index):
        """Make the model checkable"""
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable

    def setData(self, index, value, role=Qt.DisplayRole):
        """When checking an item, set the matching layer's custom property"""
        layer = super().data(index, QgsMapLayerModel.LayerRole)
        if not layer:
            return super().setData(index, value, role)

        if role == Qt.CheckStateRole:
            layer.setCustomProperty(
                "plugins/multilayerselect/excluded", value == Qt.Unchecked
            )
            return True

        return super().setData(index, value, role)

    def data(self, index, role=Qt.DisplayRole):
        """Custom data function"""
        layer = super().data(index, QgsMapLayerModel.LayerRole)
        if not layer:
            return super().data(index, role)

        # If layer name is unique, returns <layerName>, else return <layerName> (<id>)
        if role == Qt.DisplayRole:
            original_name = super().data(index, role)
            if original_name in self.non_unique_names():
                return f"{original_name} ({super().data(index, QgsMapLayerModel.LayerIdRole)})"

        # Get the icon from the layer tree view
        if role == Qt.DecorationRole:
            return icon_from_layer(layer)

        if role == Qt.CheckStateRole:
            excluded = layer.customProperty(
                "plugins/multilayerselect/excluded", False
            ) in (True, "true", "True", "1")
            return 0 if excluded else 2

        return super().data(index, role)


class SettingsDialog(QDialog, Ui_SettingsDialog):
    """Settings Dialog implementation"""

    settingsChanged = pyqtSignal()  # noqa: N815
    colorChanged = pyqtSignal()  # noqa: N815

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

        self.onlyVisibleCheckBox.setChecked(
            self.settings.value("only_visible", True, bool)
        )
        self.ignoreScaleCheckBox.setChecked(
            self.settings.value("ignore_scale", False, bool)
        )
        self.activeLayerCheckBox.setChecked(
            self.settings.value("set_active_layer", True, bool)
        )
        self.showSettingsCheckBox.setChecked(
            self.settings.value("show_settings", True, bool)
        )
        self.replaceActionsCheckBox.setChecked(
            self.settings.value("replace_actions", False, bool)
        )

        self.includeActiveLayerCheckBox.setChecked(
            self.settings.value("always_include_active_layer", True, bool)
        )

        self.layer_model = LayerModel(self)
        self.view.setModel(self.layer_model)

        # Connect signals
        self.selectionColorButton.colorChanged.connect(self.on_color_changed)
        self.onlyVisibleCheckBox.toggled.connect(self.on_only_visible_changed)
        self.ignoreScaleCheckBox.toggled.connect(self.on_ignore_scale_changed)
        self.activeLayerCheckBox.toggled.connect(self.on_active_layer_changed)
        self.showSettingsCheckBox.toggled.connect(self.on_show_settings_changed)
        self.replaceActionsCheckBox.toggled.connect(self.on_replace_actions_changed)
        self.includeActiveLayerCheckBox.toggled.connect(
            self.on_always_include_active_layer_changed
        )
        self.excludeButton.clicked.connect(self.layer_model.exlude_all)
        self.includeButton.clicked.connect(self.layer_model.include_all)

    def on_project_color_changed(self):
        """Called to update the color button when the project selection color changes,
        or when the project is read for QGIS < 3.10"""
        try:
            self.selectionColorButton.setColor(QgsProject.instance().selectionColor())
        except AttributeError:  # QGIS < 3.10
            self.selectionColorButton.setColor(iface.mapCanvas().selectionColor())

    def on_color_changed(self, color: QColor):
        """Set the project selection color from the color button"""

        try:
            QgsProject.instance().setSelectionColor(color)
            # Mark the project dirty to make it "saveable"
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

        # Will trigger the icon color change
        self.colorChanged.emit()

    def on_only_visible_changed(self, checked):
        """Update the only_visible setting"""
        self.settings.setValue("only_visible", checked)
        self.settingsChanged.emit()

    def on_active_layer_changed(self, checked):
        """Update the set_active_layer setting"""
        self.settings.setValue("set_active_layer", checked)
        self.settingsChanged.emit()

    def on_ignore_scale_changed(self, checked):
        """Update the ignore_scale setting"""
        self.settings.setValue("ignore_scale", checked)
        self.settingsChanged.emit()

    def on_show_settings_changed(self, checked):
        """Update the show_settings setting"""
        self.settings.setValue("show_settings", checked)
        self.settingsChanged.emit()

    def on_replace_actions_changed(self, checked):
        """Update the replace_actions setting"""
        self.settings.setValue("replace_actions", checked)
        self.settingsChanged.emit()

    def on_always_include_active_layer_changed(self, checked):
        """Update the replace_actions setting"""
        self.settings.setValue("always_include_active_layer", checked)
        self.settingsChanged.emit()
