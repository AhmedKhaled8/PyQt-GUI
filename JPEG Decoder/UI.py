from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys
from pyqtgraph import ImageView
from decoder import Decoder
import cv2
import numpy as np
from PIL.ImageQt import ImageQt


class UI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("picture.png"))
        self.setWindowTitle("Progressive JPEG Decoder")
        self.path = None
        self.alreadyDecoded = False
        upperLayout = QHBoxLayout()
        upperGroup = QGroupBox()
        lowerLayout = QHBoxLayout()
        lowerGroup = QGroupBox()
        mainLayout = QVBoxLayout()
        mainGroup = QGroupBox()
        self.setFixedWidth(1800)
        self.setFixedHeight(700)
        self.labels = []
        for i in range(8):
            label = QLabel()
            label.setFixedWidth(300)
            label.setFixedHeight(300)
            pixmap = QPixmap("imageblock.png")
            pixmap = pixmap.scaledToWidth(300)
            pixmap = pixmap.scaledToHeight(300)
            label.setPixmap(pixmap)
            if i <= 3:
                upperLayout.addWidget(label)
            else:
                lowerLayout.addWidget(label)
            self.labels.append(label)
        upperGroup.setLayout(upperLayout)
        lowerGroup.setLayout(lowerLayout)
        mainLayout.addWidget(upperGroup)
        mainLayout.addWidget(lowerGroup)
        buttonsLayout = QHBoxLayout()
        buttonsGroup = QGroupBox()
        self.open = QPushButton("Open")
        self.open.clicked.connect(self.openImage)
        self.start = QPushButton("Start")
        self.start.clicked.connect(self.decode)
        buttonsLayout.addWidget(self.open)
        buttonsLayout.addWidget(self.start)
        buttonsGroup.setLayout(buttonsLayout)
        mainLayout.addWidget(buttonsGroup)
        mainGroup.setLayout(mainLayout)
        
        self.infoText = QTextEdit()
        

        uiLayout = QHBoxLayout()
        uiLayout.addWidget(mainGroup)
        uiLayout.addWidget(self.infoText)
        uiGroup = QGroupBox()
        uiGroup.setLayout(uiLayout)
        self.setCentralWidget(uiGroup)

    def decode(self):
        if self.path and not self.alreadyDecoded:
            self.start.setText("Decoding, please wait...")
            if self.decoder.mode == 0XC2:
                for i in range(min(len(self.decoder.dataList), 8)):
                    dataIndex = i
                    if i == 7:
                        dataIndex = len(self.decoder.dataList) - 1
                    path = self.decoder.decodeComponents(dataIndex)
                    pixmap = QPixmap(path).scaled(300, 300, Qt.KeepAspectRatio)
                    self.labels[i].setPixmap(pixmap)
                    QApplication.processEvents()
                self.infoText.append("Decoding Done !!!!")
                self.start.setText("Start")
                self.alreadyDecoded = True

    def openImage(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.path, _ = QFileDialog.getOpenFileName(self, "Open Image", "",
                                              "Images Files (*.jpg *.jpeg)", options=options)
        if self.path:
            print(self.path)
            self.decoder = Decoder(self.path, self.infoText)
            self.decoder.run()
            print(self.decoder.mode)
            if self.decoder.mode != 0XC2:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Selected Image is BASELINE not PROGRESSIVE")
                msg.setWindowTitle("Error")
                msg.exec_()
            else:
                for i in range(8):
                    pixmap = QPixmap("imageblock.png")
                    pixmap = pixmap.scaledToWidth(300)
                    pixmap = pixmap.scaledToHeight(300)
                    self.labels[i].setPixmap(pixmap)
                self.alreadyDecoded = False
                self.infoText.clear()
                self.infoText.append("Image: {}".format(self.path))
                self.infoText.append("No. of scans: {}".format(min(len(self.decoder.dataList), 8)))


app = QApplication(sys.argv)
ui = UI()
ui.show()
sys.exit(app.exec_())


