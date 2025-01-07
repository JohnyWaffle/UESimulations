from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem, QGraphicsRectItem
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPen, QBrush, QPainter, QFont  
import numpy as np

class NetworkView(QGraphicsView):
    def __init__(self, env):
        super().__init__()
        self.env = env
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setSceneRect(-1000, -1000, 6000, 6000)  
        self.populate_scene()
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def populate_scene(self):
        self.scene.clear()
        
        for i, bs in enumerate(self.env.base_stations):
            label = chr(ord('A') + i)  
            self.scene.addEllipse(bs.x - 5, bs.y - 5, 25, 25, 
                                  QPen(Qt.GlobalColor.blue), 
                                  QBrush(Qt.GlobalColor.blue))
            self.scene.addText(label, QFont("Arial", 12)).setPos(bs.x + 10, bs.y - 10)  
            coverage_radius = 1000
            coverage_area = QGraphicsEllipseItem(bs.x - coverage_radius, bs.y - coverage_radius, 
                                                 2 * coverage_radius, 2 * coverage_radius)
            coverage_area.setPen(QPen(Qt.GlobalColor.red, 1, Qt.PenStyle.DashLine)) 
            coverage_area.setBrush(Qt.GlobalColor.transparent)
            self.scene.addItem(coverage_area)
            
            for square in bs.squares: 
                square_item = QGraphicsRectItem(square[0], square[1], 50, 50) 
                square_item.setPen(QPen(Qt.GlobalColor.green))  
                square_item.setBrush(QBrush(Qt.GlobalColor.green, Qt.BrushStyle.Dense6Pattern)) 
                self.scene.addItem(square_item)

        for i, ue in enumerate(self.env.user_equipments):
            ue_size = 25  
            self.scene.addEllipse(ue.x, ue.y, ue_size, ue_size, 
                                  QPen(Qt.GlobalColor.red), 
                                  QBrush(Qt.GlobalColor.red))
            self.scene.addText(str(i + 1), QFont("Arial", 12)).setPos(ue.x + 10, ue.y - 10)  # UE label
            if ue.serving_bs:
                base_station_pos = QPointF(ue.serving_bs.x, ue.serving_bs.y)
                ue_pos = QPointF(ue.x, ue.y)
                line = QGraphicsLineItem(base_station_pos.x(), base_station_pos.y(), ue_pos.x(), ue_pos.y())
                line.setPen(QPen(Qt.GlobalColor.gray, 1))
                self.scene.addItem(line)

    def update_scene(self):
        self.populate_scene() 

    def wheelEvent(self, event):
        factor = 1.2
        if event.angleDelta().y() < 0:
            factor = 1 / factor
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.MiddleButton:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - event.date().x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - event.date().y())
        super().mouseMoveEvent(event)
