from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ImageLayout import *
from pyqtgraph import ImageView
from ImageViewer import ImageViewer
import cv2
from defaultImage import defaultOutput
import sys


class OutputLayout(QWidget):
    """
           :param  logger: the logger of the main appliaction
           :arg    selectedImages: selected images in the image combobox
                   selectedComponents: selected components in the components comboboxes
                   scaleValues: the scale values of the two sliders
                   recievedData: the ImageData classes recieved from ImageLayout using sendImageSize
                   selectedOutput: refers to the selected output through the radio buttons (0 for first and 1 for second)
                   logger: the logger of the main application
                   outputImages: the data nparrays of the outputs
           """
    def __init__(self, logger):
        super().__init__()

        self.selectedImages = [0, 0]
        self.selectedComponents = ["Magnitude", "Phase"]
        self.scaleValues = [0.5, 0.5]
        self.recievedData = [None, None]
        self.selectedOutput = 0
        self.logger = logger
        self.ouputImages = [None, None]

        self.outputLayout = QVBoxLayout()
        self.initSliders()
        self.initOutput()


        self.setLayout(self.outputLayout)

    def initSliders(self):
        """"
        initSliders: creates two objects of SliderLayout, sets their functions and append them to the OutputLayout layout
        """
        self.sliderLayouts = [SliderLayout(0), SliderLayout(1)]
        layout = QVBoxLayout()
        groupBox = QGroupBox()
        for i in range(2):
            self.setFunctions(i)
            layout.addWidget(self.sliderLayouts[i])
        groupBox.setLayout(layout)
        self.outputLayout.addWidget(groupBox)
        self.sliderLayouts[0].slider.setEnabled(False)
        self.sliderLayouts[1].slider.setEnabled(False)
        self.sliderLayouts[0].componentCombo.setEnabled(False)
        self.sliderLayouts[1].componentCombo.setEnabled(False)
        self.sliderLayouts[0].imageCombo.setEnabled(False)
        self.sliderLayouts[1].imageCombo.setEnabled(False)


    def setFunctions(self, index):
        """
        sets the callback functions for the image and component compoboxes and the slider
        :param index: the index of the SliderLayout Class
        :return: None
        """
        self.sliderLayouts[index].imageCombo.activated[str].connect(lambda: self.selectImage(index))
        self.sliderLayouts[index].componentCombo.activated[str].connect(lambda: self.selectComponent(index))
        self.sliderLayouts[index].slider.valueChanged.connect(lambda: self.sliderMoved(index))
        self.sliderLayouts[index].slider.sliderReleased.connect(lambda: self.sliderReleased(index))

    def selectImage(self, index):
        """
        selectImage:    when image combobox is activated, it sets the selected image to the selectedImages and show the
                        output simultaneously
        :param index: the index of the parent SliderLayout
        :return: None
        """
        selectedImage = self.sliderLayouts[index].imageCombo.currentText()
        if selectedImage == "Image 1":
            self.selectedImages[index] = 0
        elif selectedImage == "Image 2":
            self.selectedImages[index] = 1
        imageChangedMessage = "Image Combobox {} has changed to {}".format(index+1, self.selectedImages[index])
        self.logger.debug(imageChangedMessage)
        self.showOutput()

    def selectComponent(self, index):
        """
        selectComponent:    when the component combobox is activated, it will set the selected component in the
                            selectedComponents and show the output. If this selected component is either Uniform
                            Magnitude or Uniform Phase, it will disable the sliders, as these components does not depend
                            on them.
        :param index: the index of the parent SliderLayout
        :return:
        """
        selectedComponent = self.sliderLayouts[index].componentCombo.currentText()
        self.selectedComponents[index] = selectedComponent
        if index == 0:
            mixType = self.getMixType(selectedComponent)
            print(mixType)
            self.sliderLayouts[1].setSecondCompo(mixType)
            self.selectedComponents[1] = self.sliderLayouts[1].componentCombo.currentText()
            self.sliderLayouts[1].slider.setEnabled(True)
        if selectedComponent == "Uniform Magnitude" or selectedComponent == "Uniform Phase":
            self.sliderLayouts[index].slider.setEnabled(False)
        else:
            self.sliderLayouts[index].slider.setEnabled(True)
        componentChangedMessage = "Component ComboBox {} of image {} changed to Image {}".format(index+1, self.selectedImages[index]+1, selectedComponent)
        self.logger.debug(componentChangedMessage)
        self.showOutput()


    def sliderMoved(self, index):
        """
        sliderMoved:    when the slider is changing its value. The label next to it changes its text to the value the
                        slider has, changing the value of the scaleValues in the index location, and show the output
                        considering the current values of the sliders.
        :param index: the index of the parent SliderLayout
        :return: None
        """
        print("Slider {}, Value {}".format(index, self.sliderLayouts[index].slider.value()))
        self.scaleValues[index] = self.sliderLayouts[index].slider.value()/100
        print(self.scaleValues[index])
        self.sliderLayouts[index].valueLabel.setText(str(self.sliderLayouts[index].slider.value())+" %")
        self.showOutput()

    def sliderReleased(self, index):
        sliderReleasedMessage = "Slider {} moved to {}%".format(index+1, self.sliderLayouts[index].slider.value())
        scale1 = self.scaleValues[0]
        scale2 = self.scaleValues[1]
        comp1 = self.selectedComponents[0]
        comp2 = self.selectedComponents[1]
        index1 = self.selectedImages[0]
        index2 = self.selectedImages[1]
        mixMessage = "Mixing {} of {} of Image {} with {} of {} of Image {}".format(scale1, comp1, index1+1, scale2, comp2, index2+1)
        self.logger.debug(sliderReleasedMessage)
        self.logger.debug(mixMessage)




    def initOutput(self):
        """"
        initOuput:  init the layout of the output result by appending the OutputLayout layout 2 radio buttons and 2
                    ImageViewer instances with indexes 0, 1
        """
        outputLayout = QVBoxLayout()
        outputBox = QGroupBox()
        radioLayout = QHBoxLayout()
        radioGroup = QGroupBox()
        self.radio1 = QRadioButton("Image 1")
        self.radio1.setChecked(True) # At the beginning, check the first image
        self.radio1.toggled.connect(self.toggleOutput)
        self.radio2 = QRadioButton("Image 2")
        self.radio2.setChecked(False)
        self.radio2.toggled.connect(self.toggleOutput)
        self.radio1.setEnabled(False)
        self.radio2.setEnabled(False)
        radioLayout.addWidget(self.radio1)
        radioLayout.addWidget(self.radio2)
        radioGroup.setLayout(radioLayout)
        outputImagesLayout = QHBoxLayout()
        self.outputImages = [ImageViewer((400, 500)), ImageViewer((400, 500))]
        data = defaultOutput()
        self.outputImages[0].image.setImage(data)
        self.outputImages[1].image.setImage(data)
        outputImagesLayout.addWidget(self.outputImages[0])
        outputImagesLayout.addWidget(self.outputImages[1])
        outputImagesBox = QGroupBox()
        outputImagesBox.setLayout(outputImagesLayout)

        self.outputLayout.addWidget(radioGroup)
        self.outputLayout.addWidget(outputImagesBox)


    def toggleOutput(self):
        """
        toggleOutput:   it's the callback function for the radio buttons. it toggles the state selectedOutput depending
                        on the selected button (output)
        :return: None
        """
        radioBtn = self.sender()
        if radioBtn.isChecked():
            if radioBtn.text() == "Image 1":
                self.selectedOutput = 0
            elif radioBtn.text() == "Image 2":
                self.selectedOutput = 1
            outputChangedMessage = "Output Image {} is now selected".format(self.selectedOutput)
            self.logger.debug(outputChangedMessage)
            self.showOutput()


    def showOutput(self):
        """
        showOutput: depending on the selected images in selectedImages and selected components in selectedComponents and
                    the sliders values in scaleValues, showOutput mixes the selected components and show the output on
                    the selected output depending on the value of selectedOutput
        :return: None
        """
        if self.recievedData[0] != None and self.recievedData[1] != None:
            mixType1 = self.getMixType(self.selectedComponents[0])
            mixType2 = self.getMixType(self.selectedComponents[1])
            # print(mixType1, mixType2)
            selected1 = self.selectedImages[0]
            complement1 = self.complementIndex(selected1)
            selected2 = self.selectedImages[1]
            complement2 = self.complementIndex(selected2)
            # print(complement2)
            mixer1 = self.getMixers(self.recievedData[selected1], self.recievedData[complement1], mixType1,
                                    self.scaleValues[0])
            mixer2 = self.getMixers(self.recievedData[selected2], self.recievedData[complement2], mixType2,
                                    self.scaleValues[1])
            result = self.multiplyMixers(mixer1, mixer2, mixType1)
            imagedata = np.abs(np.fft.ifft2(result))
            self.ouputImages[self.selectedOutput] = imagedata
            self.outputImages[self.selectedOutput].image.setImage(imagedata.T, scale=(400, 400))

    @pyqtSlot(list)
    def recieveData(self, data):
        print("recieved here also")
        self.recievedData[data[0]] = data[1]
        print(data[1].data)
        self.checkRecieved()

    def checkRecieved(self):
        if self.recievedData[0] == None or self.recievedData[1] == None:
            self.sliderLayouts[0].slider.setEnabled(False)
            self.sliderLayouts[1].slider.setEnabled(False)
            self.sliderLayouts[0].componentCombo.setEnabled(False)
            self.sliderLayouts[1].componentCombo.setEnabled(False)
            self.sliderLayouts[0].imageCombo.setEnabled(False)
            self.sliderLayouts[1].imageCombo.setEnabled(False)
            self.radio1.setEnabled(False)
            self.radio2.setEnabled(False)


        else:
            self.sliderLayouts[0].slider.setEnabled(True)
            self.sliderLayouts[1].slider.setEnabled(True)
            self.sliderLayouts[0].componentCombo.setEnabled(True)
            self.sliderLayouts[1].componentCombo.setEnabled(True)
            self.sliderLayouts[0].imageCombo.setEnabled(True)
            self.sliderLayouts[1].imageCombo.setEnabled(True)
            self.sliderLayouts[0].componentCombo.setCurrentIndex(0)
            self.sliderLayouts[1].setSecondCompo("m")
            self.selectedComponents = ["Magnitude", "Phase"]
            self.selectedImages = [0, 0]
            self.scaleValues = [0.5, 0.5]
            self.radio1.setEnabled(True)
            self.radio2.setEnabled(True)
            self.showOutput()


    def reset(self):
        data = defaultOutput()

        self.sliderLayouts[0].slider.setValue(50)
        self.sliderLayouts[1].slider.setValue(50)
        self.outputImages[0].image.setImage(data)
        self.outputImages[1].image.setImage(data)
        self.recievedData = [None, None]
        self.sliderLayouts[0].componentCombo.setCurrentIndex(0)
        self.sliderLayouts[1].setSecondCompo("m")
        self.checkRecieved()
        

    def getMixType(self, comp):
        """
        getMixType: Just send the component and then returns an abbreviation of it
        :param comp: the component
        :return: mixType: an abbreviation of the component
        """
        if comp == "Magnitude":
            mixType = "m"
        elif comp == "Phase":
            mixType = "p"
        elif comp == "Real":
            mixType = "r"
        elif comp == "Imaginary":
            mixType = "i"
        elif comp == "Uniform Magnitude":
            mixType = "um"
        elif comp == "Uniform Phase":
            mixType = "up"

        return mixType


    def getMixers(self, image1, image2, mixType, scale1):
        """
        getMixers: gets the mixer of the sent component and factor
        :param image1: the first ImageData class
        :param image2: the second ImageData class
        :param mixType: the abbreviation of the component
        :param scale1: the scale to be multiplied with the mixer
        :return: mixer: the mixer resulting of the component mixType with scale1 factor
        """
        if mixType == "m":
            mixer = image1.mag * scale1 + image2.mag*(1-scale1)
        elif mixType == "um":
            mixer = np.ones(image1.mag.shape)
        elif mixType == "p":
            mixer = image1.phase * scale1 + image2.phase * (1-scale1)
        elif mixType == "up":
            mixer = np.zeros(image1.phase.shape)
        elif mixType == "r":
            mixer = image1.real * scale1 + image2.real * (1-scale1)
        elif mixType == "i":
            mixer = image1.img * scale1 + image2.img * (1-scale1)
        return mixer

    def multiplyMixers(self, mixer1, mixer2, mixType):
        """
        multiplyMixers: combine the two mixers depending on the mixType
        :param mixer1: the mixer resulted from the mixType
        :param mixer2: the mixer resulted from the complement of the mixType
        :param mixType: the component of the first mixer, the second will be its complement
        :return:
        """
        if mixType == "m" or mixType == "um":
            output = np.multiply(mixer1, np.exp(1j*mixer2))
        elif mixType == "p" or mixType == "up":
            output = np.multiply(mixer2, np.exp(1j*mixer1))
        elif mixType == "r":
            output = mixer1 + 1j*mixer2
        elif mixType == "i":
            output = mixer2 + 1j*mixer1

        return output


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




class SliderLayout(QWidget):
    def __init__(self, index):
        super().__init__()
        slidersLayout = QHBoxLayout()
        self.imageCombo = QComboBox()
        self.imageCombo.setMinimumWidth(100)
        self.index = index
        self.imageCombo.addItem("Image 1")
        self.imageCombo.addItem("Image 2")
        self.componentCombo = QComboBox()
        self.setComponentCompo(self.index, "m")
        self.componentCombo.setMinimumWidth(120)
        self.slider = QSlider()
        self.slider.setOrientation(Qt.Horizontal)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setSingleStep(10)
        self.slider.setTickInterval(10)
        self.slider.setValue(50)
        self.valueLabel = QLabel("50 %")
        slidersLayout.addWidget(self.imageCombo)
        slidersLayout.addWidget(self.componentCombo)
        slidersLayout.addWidget(self.slider)
        slidersLayout.addWidget(self.valueLabel)
        sliderGroup = QGroupBox()
        sliderGroup.setLayout(slidersLayout)
        widgetLayout = QVBoxLayout()
        widgetLayout.addWidget(sliderGroup)
        self.setLayout(widgetLayout)

    def setComponentCompo(self, index, mixType):
        """

        :param index: the index of SliderLayout
        :param mixType: the abbreviation of the component
        :return: None
        """
        if index == 0:
            self.componentCombo.addItem("Magnitude")
            self.componentCombo.addItem("Phase")
            self.componentCombo.addItem("Real")
            self.componentCombo.addItem("Imaginary")
            self.componentCombo.addItem("Uniform Magnitude")
            self.componentCombo.addItem("Uniform Phase")

        elif index == 1:
            self.setSecondCompo(mixType)



    def clearCompo(self):
        """
        clearCompo: clears the items of the combobox
        """
        for i in range(self.componentCombo.count()):
            self.componentCombo.removeItem(0)

    def setSecondCompo(self, mixType):
        """
        :param mixType: the abbreviation of the component
        :return: None
        """
        self.clearCompo()
        if mixType == "m" or mixType == "um":
            self.componentCombo.addItem("Phase")
            self.componentCombo.addItem("Uniform Phase")

        elif mixType == "p" or mixType == "up":
            self.componentCombo.addItem("Magnitude")
            self.componentCombo.addItem("Uniform Magnitude")

        elif mixType == "r":
            self.componentCombo.addItem("Imaginary")

        elif mixType == "i":
            self.componentCombo.addItem("Real")








if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = OutputLayout()
    win.show()
    sys.exit(app.exec_())
