import cv2


def defaultData():
    """
    defaultData: shows an image of instruction to click OPEN to select images
    :return: imgData.T: the image data to be shown. The transpose related to the the pyqtgraph.ImageView class
    """
    imgData = cv2.imread("images/default.jpg", 0)

    return imgData.T

def defaultOutput():
    """
        defaultData: shows an image of instruction to select Image 1, 2 to start working with the mixer
        :return: imgData.T: the image data to be shown. The transpose related to the the pyqtgraph.ImageView class
        """
    imgData = cv2.imread("images/defaultOutput.jpg", 0)

    return imgData.T