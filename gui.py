from PyQt6.QtWidgets import (
    QApplication, QButtonGroup, QScrollArea, QSlider, QSizePolicy, QLabel, QMenu, QDockWidget, QAbstractItemView, QListWidget, QMessageBox, QMenuBar, QMainWindow, QSizePolicy, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QFileDialog
)
from PyQt6.QtGui import QPixmap, QPainter, QPen, QAction, QColor
from PyQt6.QtCore import Qt, QRect, QRectF
import sys
import math

class ImageWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.image = None
        self.scaled_image = None
        self.bound_rect = QRectF(50, 50, 160, 90)
        self.aspect_ratio = self.bound_rect.width() / self.bound_rect.height() if self.bound_rect.height() != 0 else 1
        self.dragging = False
        self.drag_start_pos = None
        self.resizing = False
        self.possible_resize_edge = None
        self.setMouseTracking(True)
        self.scale_factor = 1.0
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.prevMousePos = None
        self.pframes_info = None
        self.img_loaded = False

    def is_img_loaded(self):
        return self.img_loaded
    def load_image(self, file_path, frames_info):
        self.img_loaded = True
        self.pframes_info = frames_info
        self.scale_factor = 1.0
        self.bound_rect = QRectF(50, 50, 160, 90)
        self.image = QPixmap(file_path)
        self.scaled_image = self.image
        if self.image:
            self.setMinimumSize(self.image.size())
        self.update()
        self.pframes_info["path"] = file_path
        if "curr_frame" not in self.pframes_info:
            self.pframes_info["curr_frame"] = 0
        if "frames" not in self.pframes_info:
            self.pframes_info["frames"] = [None, None]
        
        ok = True
        for i in range(2):
            if self.pframes_info["frames"][i] == None:
                save = {}
                save["scale"] = 1.0
                save["rect_specs"] = [self.bound_rect.left(), self.bound_rect.bottom(), self.bound_rect.right(), self.bound_rect.top()]
                self.pframes_info["frames"][i] = save
        if ok:
            self.switch_frame(self.pframes_info["curr_frame"])

    def switch_frame(self, i):
        self.pframes_info["curr_frame"] = i
        data = self.pframes_info["frames"][self.pframes_info["curr_frame"]]
        self.scale_factor = data["scale"]
        self.bound_rect.setLeft(data["rect_specs"][0])
        self.bound_rect.setBottom(data["rect_specs"][1])
        self.bound_rect.setRight(data["rect_specs"][2])
        self.bound_rect.setTop(data["rect_specs"][3])

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Fill background with #171717 color
        painter.fillRect(self.rect(), QColor("#171717"))
        
        if self.image:
            # Calculate scaled image size
            available_size = self.size() * self.scale_factor
            self.scaled_image = self.image.scaled(
                available_size, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Calculate the position to center the image
            x = (self.width() - self.scaled_image.width()) / 2
            y = (self.height() - self.scaled_image.height()) / 2
            
            # Draw the scaled pixmap
            painter.drawPixmap(int(x), int(y), self.scaled_image)
            
            # Draw the red dashed rectangle
            pen = QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.SolidLine)
            pen.setDashPattern([3, 3])
            painter.setPen(pen)
            painter.drawRect(self.bound_rect)


    def scale_image(self, scale_factor):
        self.scale_factor *= scale_factor
        self.pframes_info["frames"][self.pframes_info["curr_frame"]]["scale"] = scale_factor
        self.bound_rect.moveLeft(int(self.bound_rect.left() * self.scale_factor))
        self.bound_rect.moveTop(int(self.bound_rect.top() * self.scale_factor))
        
        self.update()

    def keyPressEvent(self, event):
        if self.image:
            step = int(10 / self.scale_factor)
            if event.key() == Qt.Key.Key_W:    # Move up
                self.bound_rect.translate(0, -step)
            elif event.key() == Qt.Key.Key_S:  # Move down
                self.bound_rect.translate(0, step)
            elif event.key() == Qt.Key.Key_A:  # Move left
                self.bound_rect.translate(-step, 0)
            elif event.key() == Qt.Key.Key_D:  # Move right
                self.bound_rect.translate(step, 0)
            self.move_clamp_rect()
            self.update()

    def check_resize_clamp_rect(self, rect):
        if self.scaled_image:
            image_rect = self.scaled_image.rect()
            if rect.left() < 0:
                return True
            if rect.top() < 0:
                return True
            if rect.right() > image_rect.width():
                return True
            if rect.bottom() > image_rect.height():
                return True
    
            if rect.right() < 0:
                return True
            if rect.bottom() < 0:
                return True

            if rect.left() > image_rect.width():
                return True
            if rect.top() > image_rect.height():
                return True
        return False


    def resize_clamp_rect(self):
        if self.scaled_image:
            image_rect = self.rect()
            if self.bound_rect.left() < 0:
                self.bound_rect.setLeft(0)
            if self.bound_rect.top() < 0:
                self.bound_rect.setTop(0)
            if self.bound_rect.right() > image_rect.width():
                self.bound_rect.setRight(image_rect.width())
            if self.bound_rect.bottom() > image_rect.height():
                self.bound_rect.setBottom(image_rect.height())
    
            if self.bound_rect.right() < 0:
                self.bound_rect.setRight(0)
            if self.bound_rect.bottom() < 0:
                self.bound_rect.setBottom(0)

            if self.bound_rect.left() > image_rect.width():
                self.bound_rect.setLeft(image_rect.width())
            if self.bound_rect.top() > image_rect.height():
                self.bound_rect.setTop(image_rect.height())

    def move_clamp_rect(self):
        if self.scaled_image:
            image_rect = self.rect()
            if self.bound_rect.left() < 0:
                self.bound_rect.moveLeft(0)
            if self.bound_rect.top() < 0:
                self.bound_rect.moveTop(0)
            if self.bound_rect.right() > image_rect.width():
                self.bound_rect.moveRight(image_rect.width())
            if self.bound_rect.bottom() > image_rect.height():
                self.bound_rect.moveBottom(image_rect.height())
            if self.bound_rect.left() > image_rect.width():
                self.bound_rect.moveLeft(image_rect.width())
            if self.bound_rect.top() > image_rect.height():
                self.bound_rect.moveTop(image_rect.height())
            if self.bound_rect.right() < 0:
                self.bound_rect.moveRight(0)
            if self.bound_rect.bottom() < 0:
                self.bound_rect.moveBottom(0)
            self.pframes_info["frames"][self.pframes_info["curr_frame"]]["rect_specs"] = [self.bound_rect.left(), self.bound_rect.bottom(), self.bound_rect.right(), self.bound_rect.top()]

    def set_scale_factor(self, scale):
        self.scale_factor = scale
        self.pframes_info["frames"][self.pframes_info["curr_frame"]]["scale"] = scale

    def mousePressEvent(self, event):
        if self.detect_resize_edge(event.pos()):
            self.resizing = True
            return

        if self.image and self.bound_rect.contains(event.pos().x(), event.pos().y()):
            self.dragging = True
            self.drag_start_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            delta = event.pos() - self.drag_start_pos
            self.bound_rect.translate(delta.x(), delta.y())
            self.move_clamp_rect()
            self.drag_start_pos = event.pos()
        elif self.resizing:
            self.resize_rectangle(event.pos())
        else:
            self.detect_resize_edge(event.pos())
        self.prevMousePos = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.resizing = False
        self.possible_resize_edge = None

    def detect_resize_edge(self, pos):
        margin = 5
        if abs(self.bound_rect.left() - pos.x()) <= margin and abs(self.bound_rect.top() - pos.y()) <= margin:
            self.possible_resize_edge = 'lt'
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif abs(self.bound_rect.right() - pos.x()) <= margin and abs(self.bound_rect.bottom() - pos.y()) <= margin:
            self.possible_resize_edge = 'rb'
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif abs(self.bound_rect.left() - pos.x()) <= margin and abs(self.bound_rect.bottom() - pos.y()) <= margin:
            self.possible_resize_edge = 'lb'
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif abs(self.bound_rect.right() - pos.x()) <= margin and abs(self.bound_rect.top() - pos.y()) <= margin:
            self.possible_resize_edge = 'rt'
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.possible_resize_edge = None
            return False

        return True
        
    
    def resize_rectangle(self, pos):
        deltaX = pos.x() - self.prevMousePos.x() if self.prevMousePos != None else 0 
        deltaY = pos.y() - self.prevMousePos.y() if self.prevMousePos != None else 0
        delta = math.sqrt(deltaX ** 2 + deltaY ** 2)

        rect = QRectF(self.bound_rect)
        if self.possible_resize_edge == 'lt':
            new_width = self.bound_rect.right() - pos.x()
            new_height = new_width / self.aspect_ratio
            rect.setLeft(pos.x())
            rect.setTop(self.bound_rect.bottom() - new_height)
        elif self.possible_resize_edge == 'rb':
            new_width = pos.x() - self.bound_rect.left()
            new_height = new_width / self.aspect_ratio
            rect.setRight(pos.x())
            rect.setBottom(self.bound_rect.top() + new_height)
        elif self.possible_resize_edge == 'lb':
            new_width = self.bound_rect.right() - pos.x()
            new_height = new_width / self.aspect_ratio
            rect.setLeft(pos.x())
            rect.setBottom(self.bound_rect.top() + new_height)
        elif self.possible_resize_edge == 'rt':
            new_width = pos.x() - self.bound_rect.left()
            new_height = new_width / self.aspect_ratio
            rect.setRight(pos.x())
            rect.setTop(self.bound_rect.bottom() - new_height)
        if self.check_resize_clamp_rect(rect):
            return

        if rect.height() == 0 or (math.fabs(rect.width() / rect.height() - self.aspect_ratio) > 0.0000001):
            return 

        if self.possible_resize_edge == 'lt':
            new_width = self.bound_rect.right() - pos.x()
            new_height = new_width / self.aspect_ratio
            self.bound_rect.setLeft(pos.x())
            self.bound_rect.setTop(self.bound_rect.bottom() - new_height)
        elif self.possible_resize_edge == 'rb':
            new_width = pos.x() - self.bound_rect.left()
            new_height = new_width / self.aspect_ratio
            self.bound_rect.setRight(pos.x())
            self.bound_rect.setBottom(self.bound_rect.top() + new_height)
        elif self.possible_resize_edge == 'lb':
            new_width = self.bound_rect.right() - pos.x()
            new_height = new_width / self.aspect_ratio
            self.bound_rect.setLeft(pos.x())
            self.bound_rect.setBottom(self.bound_rect.top() + new_height)
        elif self.possible_resize_edge == 'rt':
            new_width = pos.x() - self.bound_rect.left()
            new_height = new_width / self.aspect_ratio
            self.bound_rect.setRight(pos.x())
            self.bound_rect.setTop(self.bound_rect.bottom() - new_height)

        self.resize_clamp_rect()

        self.pframes_info["frames"][self.pframes_info["curr_frame"]]["rect_specs"] = [self.bound_rect.left(), self.bound_rect.bottom(), self.bound_rect.right(), self.bound_rect.top()]


import time

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Animator")
        self.create_menu_bar()

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        control_layout = QHBoxLayout()
        self.frame1_button = QPushButton("1")
        self.frame1_button.setCheckable(True)
        self.frame1_button.setChecked(True)
        self.frame2_button = QPushButton("2")
        self.frame2_button.setCheckable(True)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True) 
        self.button_group.addButton(self.frame1_button, 0)
        self.button_group.addButton(self.frame2_button, 1)

        self.button_group.idClicked.connect(self.frame_switched)
        control_layout.addStretch()
        control_layout.addWidget(self.frame1_button)
        control_layout.addWidget(self.frame2_button)
        control_layout.addStretch()

        main_layout = QVBoxLayout(central_widget)
        main_layout.addLayout(control_layout)
        

        self.image_widget = ImageWidget()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.image_widget)
        main_layout.addWidget(scroll_area)

        # Bottom panel with slider and buttons
        bottom_panel = QHBoxLayout()

        zoom_out_button = QPushButton("-")
        zoom_out_button.clicked.connect(lambda: self.image_widget.scale_image(0.9))
        bottom_panel.addWidget(zoom_out_button)

        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(1)
        self.zoom_slider.setMaximum(200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.slider_zoom)
        bottom_panel.addWidget(self.zoom_slider)

        zoom_in_button = QPushButton("+")
        zoom_in_button.clicked.connect(lambda: self.image_widget.scale_image(1.1))
        bottom_panel.addWidget(zoom_in_button)

        main_layout.addLayout(bottom_panel)

        self.resize(800, 600)
        self.showMaximized()

        self.create_sidebar()
        self.image_path_list = []
        self.frames_info = []


    def frame_switched(self, id):
        if self.image_widget and self.image_widget.is_img_loaded():
            self.image_widget.switch_frame(id)
            self.update()

    def create_sidebar(self):
        self.image_list_widget = QListWidget()
        self.image_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.image_list_widget.itemClicked.connect(self.on_image_item_click)

        sidebar_dock = QDockWidget("", self)
        sidebar_dock.setWidget(self.image_list_widget)
        

        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        
        title_layout.addWidget(QLabel("Loaded images"))

        button = QPushButton("+") 

        button.clicked.connect(self.import_images)
        button.setFixedSize(35, 35)
        title_layout.addStretch()   
        title_layout.addWidget(button)  
        
        sidebar_dock.setTitleBarWidget(title_widget)

        sidebar_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        sidebar_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, sidebar_dock)


    def slider_zoom(self, value):
        scale_factor = value / 100
        self.image_widget.set_scale_factor(scale_factor)
        self.image_widget.update()


    def on_image_item_click(self, item):
        i = self.image_list_widget.row(item)
        if i < len(self.image_path_list):
            self.load_image(i)

    def load_image(self, i):
        print(self.frames_info)
        path = self.image_path_list[i]
    
        if self.frames_info[i]:
            fr_i = self.frames_info[i]["curr_frame"]
            if fr_i != None:
                if fr_i == 0:
                    self.frame2_button.setChecked(False)
                    self.frame1_button.setChecked(True)
                else:
                    self.frame1_button.setChecked(False)
                    self.frame2_button.setChecked(True)

        self.image_widget.load_image(path, self.frames_info[i])
        

    def open_file(self):
        QMessageBox.information(self, "Open File", "Open File action triggered")
    
    def create_menu_bar(self):
        project_menu = self.menuBar().addMenu("Project")

        new_action = QAction("New", self)
        new_action.triggered.connect(self.new_project)
        new_action.setShortcut('Ctrl+N')
        project_menu.addAction(new_action)

        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_file)
        open_action.setShortcut('Ctrl+O')
        project_menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.open_file)
        save_action.setShortcut('Ctrl+S')
        project_menu.addAction(save_action)

        project_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut('Alt+F4')
        project_menu.addAction(exit_action)

        edit_menu = self.menuBar().addMenu("Edit")

        undo_action = QAction("Undo", self)
        undo_action.setShortcut('Ctrl+Z')
        undo_action.triggered.connect(self.open_file)
        edit_menu.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.setShortcut('Ctrl+Y')
        redo_action.triggered.connect(self.open_file)
        edit_menu.addAction(redo_action)

        data_menu = self.menuBar().addMenu("Data")
        import_action = QAction("Import images", self)
        import_action.setShortcut('Ctrl+I')
        import_action.triggered.connect(self.import_images)
        data_menu.addAction(import_action)

        help_menu = self.menuBar().addMenu("About")

        about_action = QAction("About", self)
        help_menu.triggered.connect(self.open_file)

    def new_project(self):
        print("YEEES")   

    
    def import_images(self):
        a = time.monotonic()
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Open Image File", "", "Images (*.png *.xpm *.jpg *.jpeg *.bmp)"
        )
        b = time.monotonic()

        if paths:
            file_names = [f" {path.split('/')[-1]}" for path in paths]
            c = time.monotonic()
            self.image_path_list.extend(paths)
            for i in range(len(paths)):
                self.frames_info.append({})

            e = time.monotonic()

            self.image_list_widget.addItems(file_names)
            f = time.monotonic()


    def keyPressEvent(self, event):
        self.image_widget.keyPressEvent(event)



app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
