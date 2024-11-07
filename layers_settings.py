"""
/***************************************************************************
 LayersSettings
 
 Allow to manage some layers settings

        begin                : 2024-11-06
        copyright            : (C) 2024 by Jean-Marie Arsac
        email                : jmarsac@azimut.fr
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

from qgis.core import QgsMapLayer, QgsProject, QgsVectorLayer
from qgis.PyQt.QtCore import QCoreApplication, QSettings, Qt
from qgis.utils import iface


class LayersSettings:

    def __init__(self):
        self._layers_dict = dict()

    def disable_scale_based_visibility(self):
        for layer in QgsProject.instance().mapLayers().values():
            self._layers_dict[layer.id()] = layer.hasScaleBasedVisibility()
            layer.setScaleBasedVisibility(False)

    def restore_scale_based_visibility(self):
        for key in self._layers_dict.keys():
            QgsProject.instance().mapLayer(key).setScaleBasedVisibility(
                self._layers_dict[key]
            )
