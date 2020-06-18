from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys
from DataOpenCV import *
from ImageViewer import *
from defaultImage import defaultData
from pyqtgraph import ImageView


class ImageLayout(QWidget):
    """
    ImageLayout: a QWidget containing the label, OPEN button, the image viewer and the components viewer
    :param    index: the index of the image layout. First: 0, Second: 1
            logger: the logger of the main application
    :arg    data: the ImageData class
            selected: shows if ImageViewer is occupied with data or not
            index: the index of imageLayout
            selectedSize: if the image is selected set the size to compare with the other image
            imageLayout: the main layout of the image
    """
    sendData = pyqtSignal(list)
    setSize = pyqtSignal(list)


    def __init__(self, index, logger):
        super().__init__()


        self.data = None
        self.selected = False
        self.index = index
        self.selectedSize = None
        self.logger = logger
        self.imageLayout = QVBoxLayout()
        self.setLabelUI()
        self.setImageUI()


        self.setFixedSize(850, 450)
        self.setLayout(self.imageLayout)

    def setLabelUI(self):
        """
        setLabelUI initiates the UI of the labelLayout that contains the image label, component comppbox and the open
        button
        :param: self
        :return: None
        """

        labelLayout = QHBoxLayout()


        self.nameLabel = QLabel("IMAGE "+str(self.index+1))
        self.nameLabel.setStyleSheet("font-size: 16px")
        labelLayout.addWidget(self.nameLabel)

        self.combobox = QComboBox()
        self.combobox.setStyleSheet("font-size: 16px")
        self.combobox.addItem("Magnitude")
        self.combobox.addItem("Phase")
        self.combobox.addItem("Real")
        self.combobox.addItem("Imaginary")
        labelLayout.addWidget(self.combobox)
        self.combobox.setEnabled(False)             # When the image is not shown, make the component combobox disabled
        self.combobox.activated[str].connect(self.showComponent)

        openButton = QPushButton("Open")
        openButton.clicked.connect(self.openImage)
        labelLayout.addWidget(openButton)


        labelBox = QGroupBox()
        labelBox.setFixedHeight(45)
        labelBox.setLayout(labelLayout)
        self.imageLayout.addWidget(labelBox)

    def setImageUI(self):
        """
        setImageUI: sets the ui of the image by adding 2 ImageViewer Classes one for the image itself and the other for the
        component layout
        :param self
        :return none
        """
        imageViewerLayout = QHBoxLayout()


        self.imageLabel = ImageViewer()
        data = defaultData()                # defaultData returns data of the opening image
        self.imageLabel.image.setImage(data)


        imageViewerLayout.addWidget(self.imageLabel)

        self.componentLabel = ImageViewer()
        data = defaultData()
        self.componentLabel.image.setImage(data)



        imageViewerLayout.addWidget(self.componentLabel)

        imageViewerBox = QGroupBox()
        imageViewerBox.setLayout(imageViewerLayout)
        self.imageLayout.addWidget(imageViewerBox)


    def openImage(self):
        """
        openImage: opens a OpenFileDialog which returns the path of the image. Then gets the data using getImageData fn.
        make sure of some conditions regarding the size and if everthing is right, show the image. else, show an error message
        :param self
        :return: none
        """
        message = "OPEN button for image "+str(self.index+1)+" is clicked."
        self.logger.debug(message)

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", "",
                                              "Images Files (*.jpg *.jpeg)", options=options)

        if path:
            name = self.getFileName(path)

            data = getImageData(path)


            if self.selectedSize == None:
                # Here, there was no image selected. So show the image and set the size
                self.data = data
                self.imageLabel.image.setImage(self.data.data.T, scale=(400, 400))
                self.componentLabel.image.setImage(self.data.magPlot.T, scale=(400, 400))
                self.selected = True
                self.combobox.setEnabled(True)
                self.sendImageSize()
                self.nameLabel.setText("Image {}: {}".format(self.index+1, name))
                self.selectedSize = [self.data.width, self.data.height]
                firstImageSelected = "Image {}: {} is selected and shown".format(self.index+1, name)
                self.logger.debug(firstImageSelected)
                self.sendDataFunction()
                # print(self.data.width, self.data.height)

            else:
                # Now, there is already a chosen image, so we have to check the size of new image that it is compatible
                # with the first image.
                if self.selectedSize[0] == data.width and self.selectedSize[1] == data.height:
                    self.data = data
                    self.imageLabel.image.setImage(self.data.data.T, scale=(400, 400))
                    self.componentLabel.image.setImage(self.data.magPlot.T, scale=(400, 400))
                    self.nameLabel.setText("Image {}: {}".format(self.index + 1, name))
                    self.selected = True
                    self.combobox.setEnabled(True)
                    self.sendDataFunction()
                    complementIndex = self.complementIndex(self.index)
                    secondImageSelected = "Image {} is selected and it does have the same size as image {}"\
                        .format(self.index+1, complementIndex+1)
                    self.logger.debug(secondImageSelected)
                    print(self.data.width, self.data.height)
                else:
                    # Now, the new image is NOT compatible with the first chosen image. Then, an error message is show to
                    # either select another image or press RESET if he/she to work on this image
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Critical)
                    msg.setText("Please select an image with the same size as the already selected." +
                                " Please press RESET if you want to work on this image")
                    msg.setWindowTitle("Error")
                    msg.exec_()
                    complementIndex = self.complementIndex(self.index)
                    sizeErrorMessage = "You have selected an image that doesn't have the same size as Image " + str(complementIndex+1)
                    self.logger.warning(sizeErrorMessage)

        else:
            cancelMessage = "The open was closed without selecting the image"
            self.logger.debug(cancelMessage)



    def showComponent(self, comp):
        """
        showCompoenent: depending on the component selected. the component image viewer shows it.
        :param comp: comp: ('Magnitude', 'Phase', 'Real', 'Imaginary')
        :return: None
        """
        if comp == "Magnitude":
            arr = self.data.magPlot.T
        elif comp == "Phase":
            arr = self.data.phasePlot.T
        elif comp == "Real":
            arr = self.data.realPlot.T
        elif comp == "Imaginary":
            arr = self.data.imgPlot.T
        componentViewChanged = "Now Showing the {} component of image {}".format(comp, self.index+1)
        self.logger.debug(componentViewChanged)
        self.componentLabel.image.setImage(arr, scale=(400, 400))

    @pyqtSlot()
    def sendDataFunction(self):
        """"
        sendDataFunction: a signal that is emitted when an image is selected successfully and sends its ImageData class
        to the OutputLayout class.
        """
        sendList = [self.index, self.data]
        self.sendData.emit(sendList)
        print("Sent Here")

    def reset(self):
        """"
        reset: when RESET button is clicked, everything is back to the opening state to work on other images.
        """
        data = defaultData()
        self.imageLabel.image.setImage(data)
        self.componentLabel.image.setImage(data)
        self.selectedSize = None

    @pyqtSlot()
    def sendImageSize(self):
        """
        sendImageSize: a signal that is emitted when image is set to send its size to the other ImageLayoyut widget
        :return: None
        """
        imageSize = [self.data.width, self.data.height]
        sizeSetMessage = "Size set to {}x{}".format(imageSize[0], imageSize[1])
        self.logger.debug(sizeSetMessage)
        self.setSize.emit(imageSize)
        print("Size Set")

    @pyqtSlot(list)
    def setImageSize(self, size):
        """
        setImageSize: if this image doesn't have a selectedSize, then, this will tell it that an image is selected and
        sets its size to selectedSize
        :param size: the size list sent by sendImageSize signal.
        :return: None
        """
        if self.selectedSize == None:
            self.selectedSize = size
            print("Size Recieved")

    @staticmethod
    def complementIndex(index):
        """
        complementIndex takes the index and return its complement (The other index)
        :param index: the index selected
        :return int (0, 1): the other index
        """
        if index == 1:
            return 0
        elif index == 0:
            return 1

    def getFileName(self, path):
        """
        getFileName gets the file name out of its path
        :param path: the path of the file as it contains the file name
        :return: the name of the file
        """
        return path.split('.')[-2].split('/')[-1]







if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ImageLayout(0)
    win.show()
    sys.exit(app.exec_())
