"""
Helper functions
"""

from PyQt5.QtCore import QCoreApplication

from qgis.utils import iface
from qgis.core import QgsProject, QgsVectorLayer


def vector_layers():
    """ Return the list of vector layers used by the plugin """
    return (
        layer
        for layer in QgsProject.instance().mapLayers().values()
        if isinstance(layer, QgsVectorLayer)
    )


def update_status_message():
    """ Update the status bar message according to the selected features """

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
        iface.statusBarIface().showMessage(
            QCoreApplication.translate("MultiSelectTool", "No features selected")
        )
        return

    # List of active layers
    layers_str = ", ".join(l.name() for l in active_layers)

    # All selected features belong to the same layer
    if len(active_layers) == 1:
        msg = QCoreApplication.translate(
            "MultiSelectTool", "{0} features selected on layer {1}", "", total
        ).format(total, layers_str)

    # Feature selected acros several layers
    else:
        msg = QCoreApplication.translate(
            "MultiSelectTool", "{0} features selected on layers {1}", "", total
        ).format(total, layers_str)

    iface.statusBarIface().showMessage(msg)
