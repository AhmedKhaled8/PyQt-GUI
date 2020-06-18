from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys
from pyqtgraph import ImageView





class ImageViewer(QWidget):
    """
    ImageViewer: a pyqtgraph.ImageView to show the Image
    :param size: the size of the viewer
    """
    def __init__(self, size=(400, 350)):
        super().__init__()
        width = size[0]
        height = size[1]
        self.setFixedSize(width, height)
        self.image = ImageView()
        # Hide the ImageView additional figures
        self.image.ui.histogram.hide()
        self.image.ui.roiBtn.hide()
        self.image.ui.menuBtn.hide()
        self.image.ui.roiPlot.hide()
        layout = QVBoxLayout()
        layout.addWidget(self.image)
        self.setLayout(layout)
