""" Mutli Selection Map tools """

import math

from PyQt5.QtCore import Qt, QSettings, QPoint, pyqtSignal, QEvent
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy

from qgis.core import (
    QgsGeometry,
    QgsVectorLayer,
    QgsWkbTypes,
    QgsPointXY,
    QgsRectangle,
)
from qgis.gui import QgsMapTool, QgsRubberBand, QgsMapToolIdentify, QgsDoubleSpinBox
from qgis.utils import iface

from .icon_utils import cursor_from_image

from .utils import update_status_message, vector_layers


def has_moved(pos1: QPoint, pos2: QPoint, pixel_threshold=10):
    """Helper function that return true if cursor has moved between pos1 and pos2

    Args:
        pos1 (QPoint): Position of the first point
        pos2 (QPoint): Position of the second point
        pixel_threshold (int, optional): If the euclidian distance between pos1 and pos2
            is greather than threshold, the function will return True

    Returns:
        bool: True if the position has changed
    """
    return (
        math.sqrt(math.pow(pos1.x() - pos2.x(), 2) + math.pow(pos1.y() - pos2.y(), 2))
        > pixel_threshold
    )


class MultiSelectTool(QgsMapToolIdentify):
    """ Base class for multi selection tools """

    def __init__(self, canvas):
        super().__init__(canvas)

        canvas.mapToolSet.connect(self.on_map_tool_set)
        self.status_message = ""

        self.rubber = QgsRubberBand(canvas, QgsWkbTypes.PolygonGeometry)
        self.rubber2 = QgsRubberBand(canvas, QgsWkbTypes.PolygonGeometry)

    def flags(self):
        """ Override to disable ZoomRect """
        return QgsMapTool.Flag()

    def on_map_tool_set(self, new_tool, old_tool):
        """ Reset the tool when another one is set and update the status message """
        if new_tool == self:
            iface.statusBarIface().showMessage(self.status_message)
        elif old_tool == self:
            self.reset()
            iface.statusBarIface().clearMessage()

    def refresh_color(self):
        """ Update the rubberbands color """
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
        """ Reset the rubberbands """
        self.rubber.reset(QgsWkbTypes.PolygonGeometry)
        self.rubber2.reset(QgsWkbTypes.PolygonGeometry)

    def __del__(self):
        """ Reset the tool when it is destroyed """
        self.reset()

    def select(self, geom, modifiers):
        """Select the features contained in geom

        Args:
            geom (QgsGeometry): Selection Area
            modifiers (Qt.KeyboardModifiers): Which modifier keys are pressed
        """

        if isinstance(geom, QgsPointXY):
            layers = vector_layers(True)
        else:
            layers = vector_layers()

        if not layers:
            return

        # Selection Mode
        ctrl = modifiers & Qt.ControlModifier
        shift = modifiers & Qt.ShiftModifier

        # Compute the already selected features for each vector layer
        selected_dict = {layer: [layer.selectedFeatureIds(), []] for layer in layers}

        # Select by point
        if isinstance(geom, QgsPointXY):
            results = self.identify(
                QgsGeometry.fromPointXY(geom),
                QgsMapToolIdentify.TopDownStopAtFirst,
                layers,
                QgsMapToolIdentify.VectorLayer,
            )

            was_selected = False

            # Only one result on click (TopDownStopAtFirst)
            if results:
                res = results[-1]
                was_selected = res.mFeature.id() in selected_dict[res.mLayer][0]
                selected_dict[res.mLayer][1].append(res.mFeature.id())

            for layer, (_, new) in selected_dict.items():

                # If shift or ctrl pressed: toggle selection
                if shift or ctrl:
                    layer.selectByIds(
                        new,
                        QgsVectorLayer.RemoveFromSelection
                        if was_selected
                        else QgsVectorLayer.AddToSelection,
                    )

                # Otherwise, clear previous selection and select the clicked feature
                else:
                    layer.selectByIds(new)

        # Select by geometry
        else:
            results = self.identify(
                geom,
                QgsMapToolIdentify.TopDownAll,
                layers,
                QgsMapToolIdentify.VectorLayer,
            )

            for res in results:
                selected_dict[res.mLayer][1].append(res.mFeature.id())

            for layer, (_, new) in selected_dict.items():

                # SHIFT: Add newly selected features to selection
                if shift:
                    layer.selectByIds(new, QgsVectorLayer.AddToSelection)
                # CTRL: Remove newly selected features from selection
                elif ctrl:
                    layer.selectByIds(new, QgsVectorLayer.RemoveFromSelection)
                # No modifier: Clear selection and select newly selected features
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

        # If none of the layers with selected features is active and the settings is
        # enabled, set the first one as the new active layer
        if (
            active_layers
            and iface.activeLayer() not in active_layers
            and QSettings().value(
                "plugins/multilayerselect/set_active_layer", True, bool
            )
        ):
            iface.setActiveLayer(active_layers[0])

        # Display status message
        update_status_message()

    def keyPressEvent(self, event):
        """ Called when the Escape key is pressed. Reset the tool """
        # pylint: disable=invalid-name
        if event.key() == Qt.Key_Escape:
            self.reset()


class MultiSelectionAreaTool(MultiSelectTool):
    """ Point or Rectangle multi selection tool """

    def __init__(self, canvas):
        super().__init__(canvas)
        self.setCursor(
            cursor_from_image(
                ":/plugins/multilayerselect/icons/selectRectangleCursor.svg"
            )
        )
        self.ref_point = None
        self.ref_pos = None

    def canvasPressEvent(self, event):
        """ Called when the mouse is pressed. Set the ref point """
        # pylint: disable=invalid-name
        self.ref_pos = event.pos()
        self.ref_point = self.toMapCoordinates(event.pos())
        self.refresh_color()

    def canvasMoveEvent(self, event):
        """ Called when the mouse is moved. Do nothing if no ref point """
        # pylint: disable=invalid-name

        # If there is a ref point, draw the selection rectangle
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
        """ Called when the mouse is released """
        # pylint: disable=invalid-name

        # No layer, cancel selection
        layer = self.canvas().currentLayer()
        if not layer:
            self.reset()
            return

        point = self.toMapCoordinates(event.pos())

        if event.button() == Qt.LeftButton:

            # If there is a reference point, and cursor has moved since
            # select by rectangle
            if self.ref_point and has_moved(self.ref_pos, event.pos()):
                geometry = self.rubber.asGeometry()
                self.select(geometry, event.modifiers())

            # Else, select by point
            else:
                self.select(point, event.modifiers())

            self.reset()

    def reset(self):
        """ Reset the rubber and ref points """
        super().reset()
        self.ref_point = None
        self.ref_pos = None


class MultiSelectionPolygonTool(MultiSelectTool):
    """ Polygon multi selection tool. Handle freehand drawing if mouse is pressed """

    def __init__(self, canvas):
        super().__init__(canvas)
        self.setCursor(
            cursor_from_image(
                ":/plugins/multilayerselect/icons/selectPolygonCursor.svg"
            )
        )
        self.pressed = False

    def canvasPressEvent(self, event):
        """ Called when the mouse is pressed """
        # pylint: disable=invalid-name

        if event.button() == Qt.LeftButton:
            if self.rubber.numberOfVertices() == 0:
                self.refresh_color()
            point = self.toMapCoordinates(event.pos())
            self.rubber.addPoint(point)
            self.rubber2.reset(QgsWkbTypes.PolygonGeometry)
            for i in range(self.rubber.numberOfVertices()):
                self.rubber2.addPoint(self.rubber.getPoint(0, i))
            self.rubber2.addPoint(point)
            self.pressed = True

        # Validate the selection if polygon is valid (more than 2 points)
        elif event.button() == Qt.RightButton:
            if self.rubber.numberOfVertices() > 2:
                geom = self.rubber.asGeometry()
                self.select(geom, event.modifiers())
            self.reset()

    def canvasReleaseEvent(self, event):
        """ Called when the mouse is released """
        # pylint: disable=unused-argument,invalid-name
        self.pressed = False

    def canvasMoveEvent(self, event):
        """ Called when the mouse is moved """
        # pylint: disable=invalid-name

        # Get the QgsPoint from the event position
        point = self.toMapCoordinates(event.pos())

        # If mouse is pressed, add the point to the rubberband (Freehand draw)
        if self.pressed:
            self.rubber.addPoint(point)
            self.rubber2.addPoint(point)

        # Else, update the last point in the temporary rubberband (Polygoon draw)
        else:
            self.rubber2.movePoint(self.rubber2.numberOfVertices() - 1, point)


class DistanceWidget(QWidget):
    """ Widget used to manually edit the selection radius"""

    distanceChanged = pyqtSignal(float)
    distanceEditingFinished = pyqtSignal(Qt.KeyboardModifiers)
    distanceEditingCanceled = pyqtSignal()

    def __init__(self, label, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignLeft)

        if label:
            self.label = QLabel(label, self)
            self.label.setAlignment(Qt.AlignRight | Qt.AlignCenter)
            layout.addWidget(self.label)

        self.spinbox = QgsDoubleSpinBox(self)
        self.spinbox.setSingleStep(1)
        self.spinbox.setValue(0)
        self.spinbox.setMinimum(0)
        self.spinbox.setMaximum(1000000000)
        self.spinbox.setDecimals(6)
        self.spinbox.setShowClearButton(False)
        self.spinbox.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        layout.addWidget(self.spinbox)

        # connect signals
        self.spinbox.installEventFilter(self)
        self.spinbox.valueChanged.connect(self.distanceChanged.emit)

        # config focus
        self.setFocusProxy(self.spinbox)

    def set_distance(self, distance):
        """ set the selection radius """
        self.spinbox.setValue(distance)
        self.spinbox.selectAll()

    def distance(self):
        """ return he selection radius """
        return self.spinbox.value()

    def eventFilter(self, obj, event):
        """ Intercept key press event to emit our own custom signals """
        # pylint: disable=invalid-name

        if obj is self.spinbox and event.type() == QEvent.KeyPress:

            if event.key() == Qt.Key_Escape:

                self.distanceEditingCanceled.emit()
                return True

            if event.key() in (Qt.Key_Enter, Qt.Key_Return):
                # Emit the editing finished signal with modifier to handle remove
                # from selection and add to selection
                self.distanceEditingFinished.emit(event.modifiers())
                return True

        return False


class MultiSelectionRadiusTool(MultiSelectTool):
    """ Circle multi selection tool """

    def __init__(self, canvas):
        super().__init__(canvas)
        self.setCursor(
            cursor_from_image(":/plugins/multilayerselect/icons/selectRadiusCursor.svg")
        )
        self.center_point = None
        self.distance_widget: DistanceWidget = None

    def canvasMoveEvent(self, event):
        """ Called when the mouse is moved. Do nothing no center point """
        # pylint: disable=invalid-name

        # If a center point was set, update the rubberband to draw the circle
        if self.center_point:
            edge_point = self.toMapCoordinates(event.pos())
            radius = math.sqrt(self.center_point.sqrDist(edge_point))
            self.distance_widget.set_distance(radius)

    def canvasReleaseEvent(self, event):
        """ Called when the mouse is released """
        # pylint: disable=invalid-name

        # Cancel the selection on right click
        if event.button() == Qt.RightButton:
            self.reset()
            return

        layer = self.canvas().currentLayer()
        if not layer:
            self.reset()
            return

        if not self.center_point:
            self.center_point = self.toMapCoordinates(event.pos())
            self.refresh_color()
            self.create_distance_widget()
            return

        self.validate(event.modifiers())

    def validate(self, modifiers):
        """ Validate the current selection with the KeyboardModifiers """
        geometry = self.rubber.asGeometry()
        self.select(geometry, modifiers)
        self.reset()

    def reset(self):
        """ Reset the rubbers and center point """
        super().reset()
        self.center_point = None
        self.delete_distance_widget()

    def update_radius_rubberband(self, radius):
        """ Update the rubber band to draw a circle centered on self.center_point
        with radius """

        self.rubber.reset(QgsWkbTypes.PolygonGeometry)

        # Arbitrarily chose 80 segments for a smooth circle
        for i in range(80):
            theta = math.radians(i * 360 / 80)
            radius_point = QgsPointXY(
                self.center_point.x() + radius * math.cos(theta),
                self.center_point.y() + radius * math.sin(theta),
            )
            self.rubber.addPoint(radius_point, False)

        self.rubber.closePoints(True)

    def create_distance_widget(self):
        """ Create the radius edition widget """
        self.delete_distance_widget()
        self.distance_widget = DistanceWidget(self.tr("Selection radius"))

        self.distance_widget.distanceChanged.connect(self.update_radius_rubberband)
        self.distance_widget.distanceEditingFinished.connect(self.validate)
        self.distance_widget.distanceEditingCanceled.connect(self.reset)

        iface.addUserInputWidget(self.distance_widget)

        self.distance_widget.setFocus(Qt.TabFocusReason)

    def delete_distance_widget(self):
        """ Delete the radius edition widget """
        if self.distance_widget:
            self.distance_widget.deleteLater()
            self.distance_widget = None


class MultiSelectionFreehandTool(MultiSelectTool):
    """ Freehand multi selection tool """

    def __init__(self, canvas):
        super().__init__(canvas)
        self.setCursor(
            cursor_from_image(
                ":/plugins/multilayerselect/icons/selectFreehandCursor.svg"
            )
        )
        self.ref_point = None

    def canvasMoveEvent(self, event):
        """ Called when the mouse is moved. Do nothing if no ref point """
        # pylint: disable=invalid-name
        if self.ref_point:
            point = self.toMapCoordinates(event.pos())
            self.rubber.addPoint(point)

    def canvasReleaseEvent(self, event):
        """ Called when the mouse is released."""
        # pylint: disable=invalid-name

        # If right button is clicked, cancel selection
        if event.button() == Qt.RightButton:
            self.reset()
            return

        # If there is no layer, cancel selection
        layer = self.canvas().currentLayer()
        if not layer:
            self.reset()
            return

        # If there is no reference point, set it
        if not self.ref_point:
            self.ref_point = self.toMapCoordinates(event.pos())
            self.refresh_color()
            return

        # Else, validate the selection
        geometry = self.rubber.asGeometry()
        self.select(geometry, event.modifiers())
        self.reset()

    def reset(self):
        """ Reset the selection tool (rubberbands and ref point) """
        super().reset()
        self.ref_point = None
