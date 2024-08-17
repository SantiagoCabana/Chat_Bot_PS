from PyQt5.QtCore import Qt, QLineF
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen,QWheelEvent
from PyQt5.QtWidgets import QGraphicsView

class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setBackgroundBrush(QBrush(Qt.white))

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        grid_size = 100
        painter.fillRect(rect, QColor(200, 200, 200))
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)
        lines = []
        for x in range(left, int(rect.right()), grid_size):
            lines.append(QLineF(x, rect.top(), x, rect.bottom()))
        for y in range(top, int(rect.bottom()), grid_size):
            lines.append(QLineF(rect.left(), y, rect.right(), y))
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        painter.drawLines(lines)

    def wheelEvent(self, event: QWheelEvent):
        zoom_factor = 2.0
        max_zoom = 0.8  
        min_zoom = 0.3
    
        current_transform = self.transform()
        current_scale = current_transform.m11()
    
        if event.angleDelta().y() > 0:  
            if current_scale * zoom_factor <= max_zoom:
                self.scale(zoom_factor, zoom_factor)
        else:  
            if current_scale / zoom_factor >= min_zoom:
                self.scale(1 / zoom_factor, 1 / zoom_factor)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.centerOn(0, 0)
