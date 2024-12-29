from PyQt6.QtWidgets import (
    QApplication, QSizePolicy, QMainWindow, QSizePolicy, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QFileDialog
)
from PyQt6.QtGui import QPixmap, QPainter, QPen
from PyQt6.QtCore import Qt, QRect
import sys


class ImageWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.image = None
        self.rect = QRect(50, 50, 100, 100)
        self.dragging = False
        self.drag_start_pos = None
        self.resizing = False
        self.possible_resize_edge = None
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

    def load_image(self, file_path):
        self.image = QPixmap(file_path)
        if self.image:
            self.setMinimumSize(self.image.size())
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.image:
            painter.drawPixmap(0, 0, self.image)
        pen = QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.SolidLine)
        pen.setDashPattern([3, 3])
        painter.setPen(pen)
        painter.drawRect(self.rect)


    def keyPressEvent(self, event):
        if self.image:
            step = 10
            if event.key() == Qt.Key.Key_W:  # Move up
                self.rect.translate(0, -step)
            elif event.key() == Qt.Key.Key_S:  # Move down
                self.rect.translate(0, step)
            elif event.key() == Qt.Key.Key_A:  # Move left
                self.rect.translate(-step, 0)
            elif event.key() == Qt.Key.Key_D:  # Move right
                self.rect.translate(step, 0)
            self.move_clamp_rect()
            self.update()

    def resize_clamp_rect(self):
        if self.image:
            image_rect = self.image.rect()
            if self.rect.left() < 0:
                self.rect.setLeft(0)
            if self.rect.top() < 0:
                self.rect.setTop(0)
            if self.rect.right() > image_rect.width():
                self.rect.setRight(image_rect.width())
            if self.rect.bottom() > image_rect.height():
                self.rect.setBottom(image_rect.height())
            if self.rect.right() < 0:
                self.rect.setRight(0)
            if self.rect.bottom() < 0:
                self.rect.setBottom(0)
            if self.rect.left() > image_rect.width():
                self.rect.setLeft(image_rect.width())
            if self.rect.top() > image_rect.height():
                self.rect.setTop(image_rect.height())

    def move_clamp_rect(self):
        if self.image:
            image_rect = self.image.rect()
            if self.rect.left() < 0:
                self.rect.moveLeft(0)
            if self.rect.top() < 0:
                self.rect.moveTop(0)
            if self.rect.right() > image_rect.width():
                self.rect.moveRight(image_rect.width())
            if self.rect.bottom() > image_rect.height():
                self.rect.moveBottom(image_rect.height())
            if self.rect.left() > image_rect.width():
                self.rect.moveLeft(image_rect.width())
            if self.rect.top() > image_rect.height():
                self.rect.moveTop(image_rect.height())
            if self.rect.right() < 0:
                self.rect.moveRight(0)
            if self.rect.bottom() < 0:
                self.rect.moveBottom(0)

    def mousePressEvent(self, event):
        if self.detect_resize_edge(event.pos()):
            self.resizing = True
            return

        if self.image and self.rect.contains(event.pos()):
            self.dragging = True
            self.drag_start_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            delta = event.pos() - self.drag_start_pos
            self.rect.translate(delta)
            self.move_clamp_rect()
            self.drag_start_pos = event.pos()
        elif self.resizing:
            self.resize_rectangle(event.pos())
        else:
            self.detect_resize_edge(event.pos())
        self.update()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.resizing = False
        self.possible_resize_edge = None

    def detect_resize_edge(self, pos):
        margin = 5
        if abs(self.rect.left() - pos.x()) <= margin and abs(self.rect.top() - pos.y()) <= margin:
            self.possible_resize_edge = 'lt'
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif abs(self.rect.right() - pos.x()) <= margin and abs(self.rect.bottom() - pos.y()) <= margin:
            self.possible_resize_edge = 'rb'
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif abs(self.rect.left() - pos.x()) <= margin and abs(self.rect.bottom() - pos.y()) <= margin:
            self.possible_resize_edge = 'lb'
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif abs(self.rect.right() - pos.x()) <= margin and abs(self.rect.top() - pos.y()) <= margin:
            self.possible_resize_edge = 'rt'
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.possible_resize_edge = None
            return False

        return True
        
    
    def resize_rectangle(self, pos):
        if self.possible_resize_edge == 'lt':
            self.rect.setLeft(pos.x())
            self.rect.setTop(pos.y())
        elif self.possible_resize_edge == 'rb':
            self.rect.setRight(pos.x())
            self.rect.setBottom(pos.y())
        elif self.possible_resize_edge == 'lb':
            self.rect.setLeft(pos.x())
            self.rect.setBottom(pos.y())
        elif self.possible_resize_edge == 'rt':
            self.rect.setRight(pos.x())
            self.rect.setTop(pos.y())
        
        self.resize_clamp_rect()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Animator")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        button_layout = QHBoxLayout()
        load_button = QPushButton("Load Image")
        load_button.clicked.connect(self.load_image)
        button_layout.addWidget(load_button)

        main_layout.addLayout(button_layout)

        self.image_widget = ImageWidget()

        image_layout = QVBoxLayout()
        image_layout.addStretch()
        himage_layout = QHBoxLayout()
        himage_layout.addStretch()
        himage_layout.addWidget(self.image_widget)
        himage_layout.addStretch()
        image_layout.addLayout(himage_layout)
        image_layout.addStretch()
        main_layout.addLayout(image_layout)

        self.resize(800, 600)
        self.showMaximized()

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image File", "", "Images (*.png *.xpm *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.image_widget.load_image(file_path)

    def keyPressEvent(self, event):
        self.image_widget.keyPressEvent(event)



app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
