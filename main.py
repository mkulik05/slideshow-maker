from PyQt6.QtWidgets import QApplication
from gui.MainWindow import MainWindow
import sys

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()