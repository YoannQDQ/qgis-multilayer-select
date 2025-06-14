"""Helper function to generate dynamic QIcons and QCursors"""

import math
from pathlib import Path

from qgis.core import Qgis, QgsApplication
from qgis.PyQt.QtCore import QPointF, QSize
from qgis.PyQt.QtGui import QColor, QCursor, QIcon, QPainter, QPen, QPixmap, QPolygonF

DEFAULT_ICON_SIZE = QSize(48, 48)


def icon_path(icon_name) -> str:
    """Return the absolute path to an icon resource"""
    return str(Path(__file__).parent / "icons" / icon_name)


def create_icon(icon_path, color, base_size=DEFAULT_ICON_SIZE):
    """Create a selection tool icon. Paint the icon specified by icon_path over
    A small colored rectangle"""
    output_pixmap = QPixmap(base_size)
    output_pixmap.fill(QColor("transparent"))
    painter = QPainter(output_pixmap)

    ratio = int(base_size.width() / 48.0)

    base_icon = QIcon(icon_path)
    base_pixmap = base_icon.pixmap(base_size)

    stroke_color = color.darker()
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(stroke_color, 2 * ratio))
    painter.setBrush(color)
    painter.drawRect(4 * ratio, 4 * ratio, 28 * ratio, 28 * ratio)
    painter.drawPixmap(0, 0, base_pixmap)
    del painter

    icon = QIcon()
    icon.addPixmap(output_pixmap)

    return icon


def select_all_icon(color, base_size=DEFAULT_ICON_SIZE):
    """Create the QGIS Select All icon with a dynamic color"""
    output_pixmap = QPixmap(base_size)
    output_pixmap.fill(QColor("transparent"))
    painter = QPainter(output_pixmap)

    ratio = int(base_size.width() / 48.0)

    stroke_color = color.darker()
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(stroke_color, 2 * ratio))
    painter.setBrush(color)
    painter.drawRect(4 * ratio, 3 * ratio, 40 * ratio, 11 * ratio)
    painter.drawRect(4 * ratio, 19 * ratio, 40 * ratio, 11 * ratio)
    painter.drawRect(4 * ratio, 35 * ratio, 40 * ratio, 11 * ratio)
    del painter

    icon = QIcon()
    icon.addPixmap(output_pixmap)

    return icon


def invert_selection_icon(color, base_size=DEFAULT_ICON_SIZE):
    """Create the QGIS Invert Selecion icon with a dynamic color"""
    output_pixmap = QPixmap(base_size)
    output_pixmap.fill(QColor("transparent"))
    painter = QPainter(output_pixmap)

    ratio = base_size.width() / 48.0

    stroke_color = color.darker()
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(stroke_color, 2 * ratio))
    painter.setBrush(color)

    points = QPolygonF(
        [
            QPointF(4 * ratio, 8 * ratio),
            QPointF(4 * ratio, 44 * ratio),
            QPointF(40 * ratio, 44 * ratio),
        ]
    )

    painter.drawPolygon(points)

    painter.setBrush(QColor("#ddd"))
    painter.setPen(QPen(QColor("gray"), 2 * ratio))

    points = QPolygonF(
        [
            QPointF(8 * ratio, 4 * ratio),
            QPointF(44 * ratio, 4 * ratio),
            QPointF(44 * ratio, 40 * ratio),
        ]
    )
    painter.drawPolygon(points)

    del painter

    icon = QIcon()
    icon.addPixmap(output_pixmap)

    return icon


def expression_select_icon(color, base_size=DEFAULT_ICON_SIZE):
    """Create the expression icon"""
    output_pixmap = QPixmap(base_size)
    output_pixmap.fill(QColor("transparent"))
    painter = QPainter(output_pixmap)

    ratio = int(base_size.width() / 48.0)

    base_icon = QIcon(icon_path("selectExpression.svg"))
    base_pixmap = base_icon.pixmap(base_size)

    stroke_color = color.darker()
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(stroke_color, 2 * ratio))
    painter.setBrush(color)
    painter.drawRect(18 * ratio, 18 * ratio, 28 * ratio, 28 * ratio)
    painter.drawPixmap(0, 0, base_pixmap)
    del painter

    icon = QIcon()
    icon.addPixmap(output_pixmap)

    return icon


def cursor_from_image(path, active_x=6, active_y=6):
    """Create a QCursor from an icon. active_x and active_y set the cursor hotpoint"""

    # All calculations are done on 32x32 icons
    # Defaults to center, individual cursors may override
    icon = QIcon(path)
    cursor = QCursor()

    if not icon.isNull():
        # Apply scaling
        scale = Qgis.UI_SCALE_FACTOR * QgsApplication.instance().fontMetrics().height() / 32.0
        cursor = QCursor(
            icon.pixmap(math.ceil(scale * 32), math.ceil(scale * 32)),
            math.ceil(scale * active_x),
            math.ceil(scale * active_y),
        )

    return cursor
