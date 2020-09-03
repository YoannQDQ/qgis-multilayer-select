"""
Multilayer version of the QgsExpressionSelectionDialog
"""

from functools import partial

from PyQt5.QtWidgets import (
    QDialog,
    QToolButton,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QAction,
    QCheckBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from qgis.core import (
    QgsVectorLayer,
    QgsFields,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsRectangle,
    Qgis,
    QgsSettings,
    QgsFeatureRequest,
)
from qgis.gui import QgsExpressionBuilderWidget, QgsHelp
from qgis.utils import iface

from .utils import update_status_message, vector_layers


class MultiLayerSelectionExpressionBuilder(QDialog):
    """
    Multilayer version of the QgsExpressionSelectionDialog
    """

    def __init__(self):
        super().__init__(iface.mainWindow())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        self.expression_builder = QgsExpressionBuilderWidget(self)
        self.expression_builder.loadRecent("selection")

        fields = QgsFields()
        for layer in vector_layers():
            self.expression_builder.setLayer(layer)
            fields.extend(iface.activeLayer().fields())

        self.expression_builder.loadFieldNames(fields)
        self.expression_builder.setExpectedOutputFormat("Boolean")

        hlayout = QHBoxLayout()
        self.help_button = QPushButton(
            QIcon(":/images/themes/default/mActionHelpContents.svg"), self.tr("Help"),
        )
        self.help_button.clicked.connect(
            partial(QgsHelp.openHelp, "working_with_vector/expression.html")
        )
        hlayout.addWidget(self.help_button)

        self.only_active_checkbox = QCheckBox()
        self.only_active_checkbox.setText(self.tr("Only use active layer"))
        hlayout.addWidget(self.only_active_checkbox)

        hlayout.addStretch()

        self.close_button = QPushButton(self.tr("Close"))
        self.close_button.clicked.connect(self.reject)

        self.zoom_button = QPushButton(
            QIcon(":/images/themes/default/mActionZoomTo.svg"), self.tr("Zoom")
        )
        self.zoom_button.clicked.connect(self.on_zoom)
        self.select_button = QToolButton()
        self.select_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.select_action = QAction(
            QIcon(":/images/themes/default/mIconExpressionSelect.svg"),
            self.tr("Select Features"),
        )
        self.add_action = QAction(
            QIcon(":/images/themes/default/mIconSelectAdd.svg"),
            self.tr("Add to selection"),
        )
        self.remove_action = QAction(
            QIcon(":/images/themes/default/mIconSelectRemove.svg"),
            self.tr("Remove from selection"),
        )
        self.filter_action = QAction(
            QIcon(":/images/themes/default/mIconSelectIntersect.svg"),
            self.tr("Filter selection"),
        )

        self.select_button.setPopupMode(QToolButton.MenuButtonPopup)
        self.select_button.addAction(self.select_action)
        self.select_button.addAction(self.add_action)
        self.select_button.addAction(self.remove_action)
        self.select_button.addAction(self.filter_action)
        self.select_button.setDefaultAction(self.select_action)

        self.select_action.triggered.connect(self.set_selection)
        self.add_action.triggered.connect(self.add_to_selection)
        self.remove_action.triggered.connect(self.remove_from_selection)
        self.filter_action.triggered.connect(self.filter_selection)

        hlayout.addWidget(self.zoom_button)
        hlayout.addWidget(self.select_button)
        hlayout.addWidget(self.close_button)

        layout.addWidget(self.expression_builder)
        layout.addLayout(hlayout)

    def layers(self):
        """ Return the layer list used by the expression builder """

        if self.only_active_checkbox.isChecked():
            if not iface.activeLayer() or not isinstance(
                iface.activeLayer(), QgsVectorLayer
            ):
                return []
            return [iface.activeLayer()]
        return vector_layers()

    @property
    def expression(self):
        """ Returns the builder's expression as a string """
        return self.expression_builder.expressionText()

    def save_recent(self):
        """ Save the current expression in the 'Recent Expressions' section """
        self.expression_builder.saveToRecent("selection")

    def add_to_selection(self):
        """ See `select` """
        self.select(QgsVectorLayer.AddToSelection)

    def remove_from_selection(self):
        """ See `select` """
        self.select(QgsVectorLayer.RemoveFromSelection)

    def filter_selection(self):
        """ See `select` """
        self.select(QgsVectorLayer.IntersectSelection)

    def set_selection(self):
        """ See `select` """
        self.select(QgsVectorLayer.SetSelection)

    def select(self, selection_mode):
        """ Select all feature matching the current expression from every vecotr layer
        with the selection mode """
        for layer in self.layers():
            layer.selectByExpression(self.expression, selection_mode)
        self.save_recent()
        self.select_button.setDefaultAction(self.sender())
        update_status_message()

    def on_zoom(self):
        """ Zoom to the features matching the current expression"""
        if not self.expression:
            return

        # Compute the bounding box of the matching features
        bbox = QgsRectangle()
        bbox.setMinimal()
        feature_count = 0

        for layer in self.layers():

            context = QgsExpressionContext(
                QgsExpressionContextUtils.globalProjectLayerScopes(layer)
            )

            request = (
                QgsFeatureRequest()
                .setFilterExpression(self.expression)
                .setExpressionContext(context)
                .setNoAttributes()
            )

            for feat in layer.getFeatures(request):
                geom = feat.geometry()
                if geom.isNull() or geom.isEmpty():
                    continue

                rect = (
                    iface.mapCanvas()
                    .mapSettings()
                    .layerExtentToOutputExtent(layer, geom.boundingBox())
                )
                bbox.combineExtentWith(rect)
                feature_count += 1

        timeout = QgsSettings().value("qgis/messageTimeout", 5, int)

        if feature_count:
            iface.mapCanvas().zoomToFeatureExtent(bbox)

            iface.messageBar().pushMessage(
                "",
                self.tr(
                    "Zoomed to {0} matching feature(s)",
                    "matching feature count",
                    feature_count,
                ).format(feature_count),
                Qgis.Info,
                timeout,
            )

        else:
            iface.messageBar().pushMessage(
                "", self.tr("No matching features found"), Qgis.Info, timeout
            )

        self.save_recent()
