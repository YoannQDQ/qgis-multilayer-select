"""Allow to manage some layers settings"""

from contextlib import contextmanager

from qgis.core import QgsProject


@contextmanager
def disable_scale_based_visibility():
    """Context manager to disable scale based visibility for all layers"""

    scale_dict = {layer.id(): layer.hasScaleBasedVisibility() for layer in QgsProject.instance().mapLayers().values()}
    try:
        for layer in QgsProject.instance().mapLayers().values():
            layer.setScaleBasedVisibility(False)
        yield
    finally:
        for key, value in scale_dict.items():
            QgsProject.instance().mapLayer(key).setScaleBasedVisibility(value)
