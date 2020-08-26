from PyQt5.QtCore import QSize, QPointF
from PyQt5.QtGui import QIcon, QColor, QPainter, QPixmap, QPen, QPolygonF


def create_icon(icon_path, color, base_size=QSize(48, 48)):

    output_pixmap = QPixmap(base_size)
    output_pixmap.fill(QColor("transparent"))
    painter = QPainter(output_pixmap)

    ratio = base_size.width() / 48.0

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


def select_all_icon(color, base_size=QSize(48, 48)):
    output_pixmap = QPixmap(base_size)
    output_pixmap.fill(QColor("transparent"))
    painter = QPainter(output_pixmap)

    ratio = base_size.width() / 48.0

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


def invert_selection_icon(color, base_size=QSize(48, 48)):
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
