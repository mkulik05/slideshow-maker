from PyQt6.QtWidgets import (
	QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, 
	QProgressBar, QFileDialog, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt
import cv2
from animation import animate
import threading

class RenderDialog(QDialog):
	def __init__(self, frames, paths):
		super().__init__()

		self.frames = frames
		self.paths = paths

		self.setWindowTitle("Render Settings")
		self.progress_bar = None

		main_layout = QVBoxLayout(self)

		file_selection_layout = QHBoxLayout()
		self.file_input = QLineEdit()
		self.file_input.setPlaceholderText("Output file path")
		select_file_button = QPushButton("Select File")
		select_file_button.clicked.connect(self.select_output_file)
		file_selection_layout.addWidget(QLabel("Output File:"))
		file_selection_layout.addWidget(self.file_input)
		file_selection_layout.addWidget(select_file_button)
		main_layout.addLayout(file_selection_layout)

		fps_layout = QHBoxLayout()
		self.fps_input = QSpinBox()
		self.fps_input.setRange(1, 240)
		self.fps_input.setValue(30)
		self.render_finished = False
		fps_layout.addWidget(QLabel("FPS:"))
		fps_layout.addWidget(self.fps_input)

		duration_layout = QHBoxLayout()
		self.duration_input = QSpinBox()
		self.duration_input.setRange(1, 3600)
		self.duration_input.setValue(5)
		duration_layout.addWidget(QLabel("Duration (s):"))
		duration_layout.addWidget(self.duration_input)

		main_layout.addLayout(fps_layout)
		main_layout.addLayout(duration_layout)

		# Floating Point Input for Fade In/Out Duration
		fade_layout = QHBoxLayout()
		self.fade_input = QDoubleSpinBox()
		self.fade_input.setRange(0.0, 10.0)
		self.fade_input.setSingleStep(0.1)
		fade_layout.addWidget(QLabel("Fade In/Out (s):"))
		fade_layout.addWidget(self.fade_input)
		main_layout.addLayout(fade_layout)

		self.progress_bar = QProgressBar()
		self.progress_bar.setVisible(False)
		self.progress = 0
		main_layout.addWidget(self.progress_bar)

		button_layout = QHBoxLayout()
		start_button = QPushButton("Start")
		start_button.clicked.connect(self.start_rendering)
		cancel_button = QPushButton("Cancel")
		cancel_button.clicked.connect(self.reject)
		button_layout.addWidget(cancel_button)
		button_layout.addWidget(start_button)
		main_layout.addLayout(button_layout)

		self.resize(400, 300)

	def select_output_file(self):
		file_path, _ = QFileDialog.getSaveFileName(self, "Select Output File", "", "Video Files (*.mp4 *.avi *.mov)")
		if file_path:
			self.file_input.setText(file_path)

	def start_rendering(self):
		if not self.file_input.text():
			print("Please select an output file.")
			return
		self.progress_bar.setVisible(True)
		self.progress_bar.setValue(0)
		print(f"Rendering started with settings:")
		print(f"- Output File: {self.file_input.text()}")
		print(f"- FPS: {self.fps_input.value()}")
		print(f"- Duration: {self.duration_input.value()} seconds")
		print(f"- Fade In/Out: {self.fade_input.value()} seconds")

		

		t1 = threading.Thread(target=self.render)
		t1.start()

		
	def render(self):
		video = cv2.VideoWriter(self.file_input.text(), cv2.VideoWriter_fourcc(*'DIVX'), int(self.fps_input.value()), [1920, 1080])
		self.progress_bar.setValue(0) 
		self.progress = 0
		self.render_finished = False

		for i in range(len(self.frames)):
			animate(video, self.paths[i], self.frames[i], int(self.fps_input.value()), float(self.fade_input.value()), int(self.duration_input.value()))
			self.progress += 1 / len(self.frames)
			self.progress_bar.setValue(int(self.progress)) 
			self.update()
		self.progress_bar.setValue(100)
		self.render_finished = True

