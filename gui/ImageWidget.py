from PyQt6.QtWidgets import (
	QApplication, QButtonGroup, QScrollArea, QSlider, QSizePolicy, QLabel, QMenu, QDockWidget, QAbstractItemView, QListWidget, QMessageBox, QMenuBar, QMainWindow, QSizePolicy, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QFileDialog
)
import json
from PyQt6.QtGui import QPixmap, QPainter, QPen, QAction, QColor, QImage
from PyQt6.QtCore import Qt, QRect, QRectF, QPointF
import math
import copy

class ImageWidget(QWidget):
	def __init__(self, parent, change_clb):
		super().__init__(parent)
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
		self.change_clb = change_clb     

	def is_img_loaded(self):
		return self.img_loaded

	def set_rect_fulscreen(self):
		self.bound_rect.setLeft(self.rect().left() + 2)
		self.bound_rect.setRight(self.rect().right() + 2)
		self.bound_rect.setTop(self.rect().top() - 2)
		self.bound_rect.setBottom(self.rect().bottom() - 2)
		self.update()

	def center_rect(self):
		cx = self.rect().width() / 2
		cy = self.rect().height() / 2
		center_point = QPointF(cx, cy)
		self.bound_rect.moveCenter(center_point)
		self.update()

	
	def resizeEvent(self, event):
		if self.pframes_info:
			current_frame = self.pframes_info.get("curr_frame", 0)
			self.pframes_info["frames"][current_frame]["updated"] = True
			frame_data = self.pframes_info["frames"][current_frame]
			frame_data["pixmap_size"] = [self.rect().width(), self.rect().height()]
			self.change_clb()
		super().resizeEvent(event)

	def load_image(self, file_path, frames_info):
		self.img_loaded = True
		self.pframes_info = frames_info
		self.scale_factor = 1.0
		self.bound_rect = QRectF(50, 50, 160, 90)
		self.image = QPixmap(file_path)

		img_rect = self.image.rect()
		self.view_zoom = 1
		k1 = self.rect().height() / img_rect.height()
		k2 = self.rect().width() / img_rect.width()
		print(self.rect().width(), self.rect().height())
		print(k1, k2)
		print(img_rect.width(), img_rect.height())
		if k1 < 1 or k2 < 1:
			self.view_zoom = min(k1, k2)


		self.scaled_image = self.image
		if self.image:
			# self.setMinimumSize(self.image.size() * self.view_zoom)
			self.setMinimumSize(self.image.size())
		self.update()
		self.pframes_info["path"] = file_path
		self.pframes_info["view_zoom"] = self.view_zoom
		if "curr_frame" not in self.pframes_info:
			self.pframes_info["curr_frame"] = 0
		if "frames" not in self.pframes_info:
			self.pframes_info["frames"] = [None, None]
		
		ok = True
		for i in range(2):
			if self.pframes_info["frames"][i] == None:
				ok = False
				save = {}
				save["updated"] = False
				save["scale"] = 1.0
				save["pixmap_size"] = [self.rect().width(), self.rect().height()]
				save["rect_specs"] = [self.bound_rect.left(), self.bound_rect.bottom(), self.bound_rect.right(), self.bound_rect.top()]
				self.pframes_info["frames"][i] = save
		if ok:
			self.pframes_info["frames"][i]["pixmap_size"] = [self.rect().width(), self.rect().height()]
			self.switch_frame(self.pframes_info["curr_frame"])

	def switch_frame(self, i):
		if i == 1 and not self.pframes_info["frames"][1]["updated"]:
			self.pframes_info["frames"][1] = copy.deepcopy(self.pframes_info["frames"][0])
			self.change_clb()
		self.pframes_info["curr_frame"] = i
		data = self.pframes_info["frames"][self.pframes_info["curr_frame"]]
		self.scale_factor = data["scale"]
		self.bound_rect.setLeft(data["rect_specs"][0])
		self.bound_rect.setBottom(data["rect_specs"][1])
		self.bound_rect.setRight(data["rect_specs"][2])
		self.bound_rect.setTop(data["rect_specs"][3])

	def paintEvent(self, event):

		painter = QPainter(self)
		
		painter.fillRect(self.rect(), QColor("#171717"))
		
		if self.image:
			self.scaled_image = self.image.scaled(
				self.image.rect().size() * self.scale_factor * 1,#self.view_zoom, 
				Qt.AspectRatioMode.KeepAspectRatio, 
				Qt.TransformationMode.SmoothTransformation
			)
			
			x = (self.width() - self.scaled_image.width()) / 2
			y = (self.height() - self.scaled_image.height()) / 2

			painter.drawPixmap(int(x), int(y), self.scaled_image)
		
			pen = QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.SolidLine)
			pen.setDashPattern([3, 3])
			painter.setPen(pen)
			painter.drawRect(self.bound_rect)


	def scale_image(self, scale_factor):
		center_x = self.rect().center().x()
		center_y = self.rect().center().y()

		if self.scale_factor * scale_factor > 2 or self.scale_factor * scale_factor < 0.2:
			return
		self.set_scale_factor(self.scale_factor * scale_factor)
		self.bound_rect.moveLeft(int(self.bound_rect.left() * self.scale_factor))
		self.bound_rect.moveTop(int(self.bound_rect.top() * self.scale_factor))
		if self.scaled_image:
			new_width = self.scaled_image.width() * self.scale_factor
			new_height = self.scaled_image.height() * self.scale_factor
			self.pframes_info["frames"][self.pframes_info["curr_frame"]]["updated"] = True
			self.pframes_info["frames"][self.pframes_info["curr_frame"]]["rect_specs"] = [self.bound_rect.left(), self.bound_rect.bottom(), self.bound_rect.right(), self.bound_rect.top()]
			self.change_clb()
		if self.parent():
			scroll_area = self.parent().findChild(QScrollArea)
			if scroll_area:
				horizontal_scrollbar = scroll_area.horizontalScrollBar()
				vertical_scrollbar = scroll_area.verticalScrollBar()

				# Get the current center position of the image
				current_center_x = scroll_area.horizontalScrollBar().value() + (scroll_area.width() / 2)
				current_center_y = scroll_area.verticalScrollBar().value() + (scroll_area.height() / 2)

				# Calculate new positions based on the scale factor
				new_center_x = current_center_x * scale_factor
				new_center_y = current_center_y * scale_factor

				# Set the new scroll bar values to maintain the center position
				horizontal_scrollbar.setValue(new_center_x - (scroll_area.width() / 2))
				vertical_scrollbar.setValue(new_center_y - (scroll_area.height() / 2))
		else:
			print("Nah")
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
			image_rect = self.rect()
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
			self.pframes_info["frames"][self.pframes_info["curr_frame"]]["updated"] = True
			self.pframes_info["frames"][self.pframes_info["curr_frame"]]["rect_specs"] = [self.bound_rect.left(), self.bound_rect.bottom(), self.bound_rect.right(), self.bound_rect.top()]

			self.change_clb()

	def set_scale_factor(self, scale):
		self.scale_factor = scale
		self.pframes_info["frames"][self.pframes_info["curr_frame"]]["updated"] = True
		self.pframes_info["frames"][self.pframes_info["curr_frame"]]["scale"] = scale
		self.change_clb()

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
		self.change_clb()

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

		self.pframes_info["frames"][self.pframes_info["curr_frame"]]["updated"] = True
		self.pframes_info["frames"][self.pframes_info["curr_frame"]]["rect_specs"] = [self.bound_rect.left(), self.bound_rect.bottom(), self.bound_rect.right(), self.bound_rect.top()]



