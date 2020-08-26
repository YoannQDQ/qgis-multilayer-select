import math

from PyQt5.QtGui import QCursor, QColor, QIcon, QCursor
from PyQt5.QtCore import Qt, pyqtSignal, QSettings, QPoint
from PyQt5.QtWidgets import QAction

from qgis.core import (
    QgsGeometry,
    QgsFeature,
    QgsVectorLayer,
    QgsProject,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsWkbTypes,
    QgsPoint,
    QgsPointXY,
    QgsApplication,
    QgsRectangle,
    Qgis,
)
from qgis.gui import QgsMapTool, QgsRubberBand, QgsMapToolIdentify
from qgis.utils import iface


def cursorFromImage(path, activeX=6, activeY=6):

    # All calculations are done on 32x32 icons
    # Defaults to center, individual cursors may override

    icon = QIcon(path)
    cursor = QCursor()

    if not icon.isNull():
        # Apply scaling
        scale = (
            Qgis.UI_SCALE_FACTOR
            * QgsApplication.instance().fontMetrics().height()
            / 32.0
        )
        cursor = QCursor(
            icon.pixmap(math.ceil(scale * 32), math.ceil(scale * 32)),
            math.ceil(scale * activeX),
            math.ceil(scale * activeY),
        )

    return cursor


def hasMoved(pos1, pos2):
    return (
        math.sqrt(math.pow(pos1.x() - pos2.x(), 2) + math.pow(pos1.y() - pos2.y(), 2))
        > 10
    )


class MultiSelectTool(QgsMapToolIdentify):
    def __init__(self, canvas):
        super().__init__(canvas)

        canvas.mapToolSet.connect(self.onMapToolSet)
        self.status_message = self.tr("")

        self.rubber = QgsRubberBand(canvas, QgsWkbTypes.PolygonGeometry)
        self.rubber2 = QgsRubberBand(canvas, QgsWkbTypes.PolygonGeometry)

    def flags(self):
        return QgsMapTool.Flag()

    def onMapToolSet(self, newTool, oldTool):
        if newTool == self:
            iface.statusBarIface().showMessage(self.status_message)
        elif oldTool == self:
            self.reset()
            iface.statusBarIface().clearMessage()

    def refresh_color(self):
        stroke_color = self.canvas().selectionColor().darker(150)
        fill_color = self.canvas().selectionColor()
        fill_color.setAlphaF(0.2)
        self.rubber.setColor(fill_color)
        self.rubber.setStrokeColor(stroke_color)
        self.rubber.setWidth(1)
        self.rubber2.setColor(fill_color)
        self.rubber2.setStrokeColor(stroke_color)
        self.rubber2.setLineStyle(Qt.DotLine)
        self.rubber2.setWidth(1)

    def reset(self):
        self.rubber.reset(QgsWkbTypes.PolygonGeometry)
        self.rubber2.reset(QgsWkbTypes.PolygonGeometry)

    def __del__(self):
        self.reset()

    def select(self, geom, modifiers):

        # SelectionMode
        ctrl = modifiers & Qt.ControlModifier
        shift = modifiers & Qt.ShiftModifier

        selected_dict = {
            layer: [layer.selectedFeatureIds(), []]
            for layer in QgsProject.instance().mapLayers().values()
            if isinstance(layer, QgsVectorLayer)
        }

        if isinstance(geom, QgsPointXY):
            results = self.identify(
                QgsGeometry.fromPointXY(geom),
                QgsMapToolIdentify.TopDownStopAtFirst,
                QgsMapToolIdentify.VectorLayer,
            )

            was_selected = False

            # Only one result on click (TopDownStopAtFirst)
            if results:
                res = results[-1]
                was_selected = res.mFeature.id() in selected_dict[res.mLayer][0]
                selected_dict[res.mLayer][1].append(res.mFeature.id())

            for layer, (_, new) in selected_dict.items():
                if shift or ctrl:
                    layer.selectByIds(
                        new,
                        QgsVectorLayer.RemoveFromSelection
                        if was_selected
                        else QgsVectorLayer.AddToSelection,
                    )
                else:
                    layer.selectByIds(new)

        else:
            results = self.identify(
                geom, QgsMapToolIdentify.TopDownAll, QgsMapToolIdentify.VectorLayer,
            )

            for res in results:
                selected_dict[res.mLayer][1].append(res.mFeature.id())

            for layer, (_, new) in selected_dict.items():
                if shift:
                    layer.selectByIds(new, QgsVectorLayer.AddToSelection)
                elif ctrl:
                    layer.selectByIds(new, QgsVectorLayer.RemoveFromSelection)
                else:
                    layer.selectByIds(new)

        # Get the list of layers with at least one selected feature
        active_layers = []
        total_selected_feature_count = 0
        for layer, (_, new) in selected_dict.items():
            count = layer.selectedFeatureCount()
            if count > 0:
                total_selected_feature_count += count
                active_layers.append(layer)

        # If none of the layers with selected features is active and the settings is enabled
        # Set the first one as the new active layer
        if (
            active_layers
            and iface.activeLayer() not in active_layers
            and QSettings().value(
                "plugins/multilayerselect/set_active_layer", True, bool
            )
        ):
            iface.setActiveLayer(active_layers[0])

        # Display status message
        if total_selected_feature_count == 0:
            iface.statusBarIface().showMessage(self.tr("No features selected"))
        else:

            if len(active_layers) > 1:
                iface.statusBarIface().showMessage(
                    self.tr(
                        "{0} features selected on layers {1}",
                        "",
                        total_selected_feature_count,
                    ).format(
                        total_selected_feature_count,
                        ", ".join(l.name() for l in active_layers),
                    )
                )
            else:

                iface.statusBarIface().showMessage(
                    self.tr(
                        "{0} features selected on layer {1}",
                        "",
                        total_selected_feature_count,
                    ).format(
                        total_selected_feature_count,
                        ", ".join(l.name() for l in active_layers),
                    )
                )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reset()
            iface.mainWindow().findChild(QAction, "mActionPan").trigger()


class MultiSelectionPolygonTool(MultiSelectTool):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.setCursor(
            cursorFromImage(":/plugins/multilayerselect/icons/selectPolygonCursor.svg")
        )

    def canvasPressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.rubber.numberOfVertices() == 0:
                self.refresh_color()
            point = self.toMapCoordinates(event.pos())
            self.rubber.addPoint(point)
            self.rubber2.reset(QgsWkbTypes.PolygonGeometry)
            for i in range(self.rubber.numberOfVertices()):
                self.rubber2.addPoint(self.rubber.getPoint(0, i))
            self.rubber2.addPoint(point)

        elif event.button() == Qt.RightButton:
            if self.rubber.numberOfVertices() > 2:
                geom = self.rubber.asGeometry()
                self.select(geom, event.modifiers())
            self.reset()

    def canvasMoveEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        self.rubber2.movePoint(self.rubber2.numberOfVertices() - 1, point)


class MultiSelectionAreaTool(MultiSelectTool):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.setCursor(
            cursorFromImage(
                ":/plugins/multilayerselect/icons/selectRectangleCursor.svg"
            )
        )
        self.ref_point = None
        self.ref_pos = None

    def canvasPressEvent(self, event):
        self.ref_pos = event.pos()
        self.ref_point = self.toMapCoordinates(event.pos())
        self.refresh_color()

    def canvasMoveEvent(self, event):

        # Si on a un point de référence, on est en train de sélectionner
        if self.ref_point:
            self.rubber.reset(QgsWkbTypes.PolygonGeometry)
            point = self.toMapCoordinates(event.pos())
            minX = min(point.x(), self.ref_point.x())
            maxX = max(point.x(), self.ref_point.x())
            minY = min(point.y(), self.ref_point.y())
            maxY = max(point.y(), self.ref_point.y())
            rect = QgsRectangle(minX, minY, maxX, maxY)
            self.rubber.addGeometry(QgsGeometry.fromRect(rect), None)

    def canvasReleaseEvent(self, event):

        layer = self.canvas().currentLayer()
        if not layer:
            self.reset()
            return

        point = self.toMapCoordinates(event.pos())

        if event.button() == Qt.LeftButton:

            # On est en train de dessiner un rectangle de sélection
            if self.ref_point and hasMoved(self.ref_pos, event.pos()):
                geometry = self.rubber.asGeometry()
                self.select(geometry, event.modifiers())

            else:
                self.select(point, event.modifiers())

            self.reset()

    def reset(self):
        super().reset()
        self.ref_point = None
        self.ref_pos = None


class MultiSelectionRadiusTool(MultiSelectTool):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.setCursor(
            cursorFromImage(":/plugins/multilayerselect/icons/selectRadiusCursor.svg")
        )
        self.ref_point = None

    def canvasMoveEvent(self, event):

        # Si on a un point de référence, on est en train de sélectionner
        if self.ref_point:
            edge_point = self.toMapCoordinates(event.pos())
            radius = math.sqrt(self.ref_point.sqrDist(edge_point))
            self.updateRadiusRubberband(radius)

    def canvasReleaseEvent(self, event):

        if event.button() == Qt.RightButton:
            self.reset()
            return

        layer = self.canvas().currentLayer()
        if not layer:
            self.reset()
            return

        if not self.ref_point:
            self.ref_point = self.toMapCoordinates(event.pos())
            self.refresh_color()
            return

        geometry = self.rubber.asGeometry()
        self.select(geometry, event.modifiers())
        self.reset()

    def reset(self):
        super().reset()
        self.ref_point = None

    def updateRadiusRubberband(self, radius):
        self.rubber.reset(QgsWkbTypes.PolygonGeometry)
        for i in range(80):

            # theta = i * ( 2.0 * M_PI / RADIUS_SEGMENTS );
            theta = math.radians(i * 360 / 80)
            radiusPoint = QgsPointXY(
                self.ref_point.x() + radius * math.cos(theta),
                self.ref_point.y() + radius * math.sin(theta),
            )
            self.rubber.addPoint(radiusPoint, False)

        self.rubber.closePoints(True)


class MultiSelectionFreehandTool(MultiSelectTool):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.setCursor(
            cursorFromImage(":/plugins/multilayerselect/icons/selectFreehandCursor.svg")
        )
        self.ref_point = None

    def canvasMoveEvent(self, event):

        # Si on a un point de référence, on est en train de sélectionner
        if self.ref_point:
            point = self.toMapCoordinates(event.pos())
            self.rubber.addPoint(point)

    def canvasReleaseEvent(self, event):

        if event.button() == Qt.RightButton:
            self.reset()
            return

        layer = self.canvas().currentLayer()
        if not layer:
            self.reset()
            return

        if not self.ref_point:
            self.ref_point = self.toMapCoordinates(event.pos())
            self.refresh_color()
            return

        geometry = self.rubber.asGeometry()
        self.select(geometry, event.modifiers())
        self.reset()

    def reset(self):
        super().reset()
        self.ref_point = None

    def updateRadiusRubberband(self, radius):
        self.rubber.reset(QgsWkbTypes.PolygonGeometry)
        for i in range(80):

            # theta = i * ( 2.0 * M_PI / RADIUS_SEGMENTS );
            theta = math.radians(i * 360 / 80)
            radiusPoint = QgsPointXY(
                self.ref_point.x() + radius * math.cos(theta),
                self.ref_point.y() + radius * math.sin(theta),
            )
            self.rubber.addPoint(radiusPoint, False)

        self.rubber.closePoints(True)
