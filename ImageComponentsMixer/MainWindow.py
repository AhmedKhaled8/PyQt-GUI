from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ImageLayout import *
from OutputLayout import *
import logging

import sys


class MainWindow(QMainWindow):
    resetSignal = pyqtSignal(str)
    logging.basicConfig(filename="logging.log", format='%(asctime)s %(message)s', filemode='w')

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        self.logger.debug("Application Started")

        sshFile = "style.qss"
        fh = open(sshFile, "r")
        self.setStyleSheet(fh.read())
        self.setWindowIcon(QIcon("images/logos/logo.png"))
        self.setWindowTitle("Image Components Mixer")

        mainLayout = QHBoxLayout()
        mainBox = QGroupBox()
        self.im1 = ImageLayout(0, self.logger)
        self.im2 = ImageLayout(1, self.logger)
        self.im1.setSize.connect(self.im2.setImageSize)
        self.im2.setSize.connect(self.im1.setImageSize)
        reset = QPushButton("RESET")
        reset.setFixedHeight(30)
        reset.clicked.connect(self.resetApp)
        inputLayout = QVBoxLayout()
        inputLayout.addWidget(self.im1)
        inputLayout.addWidget(self.im2)
        inputLayout.addWidget(reset)
        inputBox = QGroupBox()
        inputBox.setLayout(inputLayout)
        mainLayout.addWidget(inputBox)
        self.output = OutputLayout(self.logger)
        self.im1.sendData.connect(self.output.recieveData)
        self.im2.sendData.connect(self.output.recieveData)
        mainLayout.addWidget(self.output)
        mainBox.setLayout(mainLayout)
        self.setCentralWidget(mainBox)


    def resetApp(self):
        self.logger.debug("RESET Button clicked")
        self.im1.reset()
        self.im2.reset()
        self.output.reset()






if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

