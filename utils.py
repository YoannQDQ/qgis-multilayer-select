"""
Helper functions
"""

from qgis.PyQt.QtCore import QCoreApplication, Qt, QSettings

from qgis.utils import iface
from qgis.core import QgsProject, QgsVectorLayer, QgsMapLayer


def vector_layers(only_visible=None):
    """Return the list of vector layers used by the plugin"""

    settings = QSettings()
    settings.beginGroup("plugins/multilayerselect")
    include_active = settings.value("always_include_active_layer", True, bool)

    if only_visible is None:
        only_visible = settings.value("only_visible", True, bool)

    return [
        layer_node.layer()
        for layer_node in QgsProject.instance().layerTreeRoot().findLayers()
        if isinstance(layer_node.layer(), QgsVectorLayer)
        and (not only_visible or layer_node.isVisible())
        and (
            (layer_node.layer() == iface.activeLayer() and include_active)
            or not layer_node.layer().customProperty("plugins/multilayerselect/excluded", False)
            in (True, "true", "True", "1")
        )
    ]


def update_status_message():
    """Update the status bar message according to the selected features"""

    active_layers = []
    total = 0

    # Get the list of layers with at least one selected feature
    for layer in QgsProject.instance().mapLayers().values():
        if isinstance(layer, QgsVectorLayer):
            count = layer.selectedFeatureCount()
            if count > 0:
                total += count
                active_layers.append(layer)

    # No feature selected
    if not active_layers:
        iface.statusBarIface().showMessage(QCoreApplication.translate("MultiSelectTool", "No features selected"))
        return

    # List of active layers
    layers_str = ", ".join(layer.name() for layer in active_layers)

    # All selected features belong to the same layer
    if len(active_layers) == 1:
        msg = QCoreApplication.translate("MultiSelectTool", "{0} features selected on layer {1}", "", total).format(
            total, layers_str
        )

    # Feature selected acros several layers
    else:
        msg = QCoreApplication.translate("MultiSelectTool", "{0} features selected on layers {1}", "", total).format(
            total, layers_str
        )

    iface.statusBarIface().showMessage(msg)


def icon_from_layer(layer: QgsMapLayer):
    """Get the layer icon from the layer tree"""
    layer_node = QgsProject.instance().layerTreeRoot().findLayer(layer)
    treemodel = iface.layerTreeView().layerTreeModel()
    index = treemodel.node2index(layer_node)
    return treemodel.data(index, Qt.DecorationRole)
