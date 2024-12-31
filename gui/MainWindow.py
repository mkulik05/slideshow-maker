from PyQt6.QtWidgets import (
	QDialog, QApplication, QListWidgetItem,QButtonGroup, QScrollArea, QSlider, QSizePolicy, QLabel, QMenu, QDockWidget, QAbstractItemView, QListWidget, QMessageBox, QMenuBar, QMainWindow, QSizePolicy, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QFileDialog
)
import json
from PyQt6.QtGui import QPixmap, QPainter, QPen, QAction, QColor, QImage
from PyQt6.QtCore import Qt, QRect, QRectF
import math
import cv2
import numpy as np
import copy
import hashlib
import time
from animation import animate_preview
from gui.ImageWidget import ImageWidget
from gui.RenderDialog import RenderDialog
import threading

def calculate_hash(data):
	json_string = json.dumps(data, sort_keys=True) 
	return hashlib.md5(json_string.encode()).hexdigest()


class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()

		self.currSelectedImgI = None

		self.setWindowTitle("Animator - Unsaved *")
		self.create_menu_bar()

		# Central Widget
		central_widget = QWidget()
		self.setCentralWidget(central_widget)
		
		control_layout = QHBoxLayout()

		self.fullscreen_button = QPushButton("Fullscreen")
		self.fullscreen_button.clicked.connect(self.fullscreen)
		self.center_button = QPushButton("Center")
		self.center_button.clicked.connect(self.center)
		self.preview_button = QPushButton("View preview")
		self.preview_button.clicked.connect(self.preview)
		self.frame1_button = QPushButton("1")
		self.frame1_button.setCheckable(True)
		self.frame1_button.setChecked(True)
		self.frame2_button = QPushButton("2")
		self.frame2_button.setCheckable(True)

		self.button_group = QButtonGroup(self)
		self.button_group.setExclusive(True) 
		self.button_group.addButton(self.frame1_button, 0)
		self.button_group.addButton(self.frame2_button, 1)

		self.view_zoom = 1

		self.button_group.idClicked.connect(self.frame_switched)
		self.changedTitle2Unsaved = False
		self.project_saved = True
		self.autosave = False
		control_layout.addStretch()
		control_layout.addWidget(self.center_button)
		control_layout.addWidget(self.fullscreen_button)
		control_layout.addWidget(self.frame1_button)
		control_layout.addWidget(self.frame2_button)
		control_layout.addWidget(self.preview_button)
		control_layout.addStretch()

		main_layout = QVBoxLayout(central_widget)
		main_layout.addLayout(control_layout)
		

		self.scroll_area = QScrollArea()
		self.image_widget = ImageWidget(self.scroll_area, lambda: self.project_modified())
		self.scroll_area.setWidgetResizable(True)
		self.scroll_area.setWidget(self.image_widget)
		main_layout.addWidget(self.scroll_area)

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
		self.assosiatedFilePath = None
		self.project_name = None

	def project_modified(self):
		if self.autosave:
			self.save_file()
			return
		self.project_saved = False
		if not self.changedTitle2Unsaved:
			self.changedTitle2Unsaved = True
			self.setWindowTitle("Animator - " + (self.project_name or "Unsaved") + " *")
			
	def fullscreen(self):
		self.image_widget.set_rect_fulscreen()
	
	def center(self):
		self.image_widget.center_rect()


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
		
		path = self.image_path_list[i]
		self.currSelectedImgI = i
		if self.frames_info[i]:

			fr_i = self.frames_info[i]["curr_frame"]
			if fr_i != None:
				if fr_i == 0:
					self.frame2_button.setChecked(False)
					self.frame1_button.setChecked(True)
				else:
					self.frame1_button.setChecked(False)
					self.frame2_button.setChecked(True)
			else:
				self.frame2_button.setChecked(False)
				self.frame1_button.setChecked(True)

		item = self.image_list_widget.item(i)
		if item:
			item.setForeground(QColor("grey"))

		self.image_widget.load_image(path, self.frames_info[i])
		

	def open_file(self):
		path, _ = QFileDialog.getOpenFileName(
			self, "Open project", "", "Project (*.project)"
		)
		if path:
			with open(path, "r") as file:
				loaded = json.load(file)
			saved_hash = loaded.get("hash")
			del loaded["hash"]
			recalculated_hash = calculate_hash(loaded)
			if saved_hash != recalculated_hash:
				print("Involid cache")
				return
			
			self.image_widget.scaled_image = None
			self.image_widget.image = None
			self.frames_info = loaded["frames"]
			self.image_path_list = loaded["img_paths"]
			self.image_list_widget.clear()
			for i in range(len(self.image_path_list)):
				item = QListWidgetItem(self.image_path_list[i].split('/')[-1])
				self.image_list_widget.addItem(item)
			
			self.assosiatedFilePath = path
			self.project_name = self.assosiatedFilePath.split('/')[-1]
			self.changedTitle2Unsaved = False
			self.setWindowTitle("Animator - " + self.project_name)
		
	
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
		save_action.triggered.connect(self.save_file)
		save_action.setShortcut('Ctrl+S')
		project_menu.addAction(save_action)

		project_menu.addSeparator()

		autosave_action = QAction("Autosave", self)
		autosave_action.setCheckable(True)  
		autosave_action.setChecked(False)  
		autosave_action.toggled.connect(self.toggle_autosave)  
		project_menu.addAction(autosave_action)

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

		render_menu = self.menuBar().addMenu("Render")
		render_menu.aboutToShow.connect(self.render)

	def render(self):
		dialog = RenderDialog(self.frames_info, self.image_path_list)
		if dialog.exec() == QDialog.DialogCode.Accepted:
			print("Rendering completed and dialog accepted.")
		else:
			print("Rendering canceled.")  


	def save_file(self):
		if self.assosiatedFilePath == None:
			file_path, _ = QFileDialog.getSaveFileName(
				self, 
				"Save Project File",                # Dialog title
				"",                                 # Default directory
				"Project Files (*.project)",       # File filter
			)
		
			if file_path:  
				if not file_path.endswith('.project'):  
					file_path += '.project'
				self.assosiatedFilePath = file_path
			else:
				return

		data = {}
		data["img_paths"] = self.image_path_list
		data["frames"] = self.frames_info
		hash_value = calculate_hash(data) 
		data["hash"] = hash_value       

		with open(self.assosiatedFilePath, "w") as file:
			json.dump(data, file, indent=4)

		self.project_name = self.assosiatedFilePath.split('/')[-1]
		self.changedTitle2Unsaved = False
		self.setWindowTitle("Animator - " + self.project_name)
		self.project_saved = True

	def new_project(self):
		print("YEEES")   

	def toggle_autosave(self, checked):
		self.autosave = checked
		self.save_file()

	def import_images(self):
		a = time.monotonic()
		paths, _ = QFileDialog.getOpenFileNames(
			self, "Open Image File", "", "Images (*.png *.xpm *.jpg *.jpeg *.bmp)"
		)
		b = time.monotonic()

		if paths:
			file_names = [f" {path.split('/')[-1]}" for path in paths]
			self.image_path_list.extend(paths)
			for i in range(len(paths)):
				self.frames_info.append({})
				item = QListWidgetItem(paths[i].split('/')[-1])
				self.image_list_widget.addItem(item)
		
			
			self.project_modified()

	def preview(self):
		print("Space pressed")
		if self.currSelectedImgI == None:
			print(" - No image")
			return
		animate_preview(self.frames_info[self.currSelectedImgI], self.image_path_list[self.currSelectedImgI])
		print(" - Finished animation")

	def keyPressEvent(self, event):
		if event.key() == Qt.Key.Key_Space:
			self.preview()
		self.image_widget.keyPressEvent(event)
	
	def closeEvent(self, event):
		if not self.project_saved:
			reply = QMessageBox.question(
				self,
				"Save project?",
				"You have unsaved changes. Do you want to save them?",
				QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
				QMessageBox.StandardButton.Yes,
			)
			if reply == QMessageBox.StandardButton.Yes:
				self.save_file()
				event.accept()
			elif reply == QMessageBox.StandardButton.No:
				event.accept()
			else:
				event.ignore()
		else:
			event.accept()