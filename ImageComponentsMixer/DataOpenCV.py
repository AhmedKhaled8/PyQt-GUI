import cv2
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from pyqtgraph import ImageView


class ImageData:
    def __init__(self, data, width, height, fft, mag, magPlot, phase,
                 phasePlot, real, realPlot, img, imgPlot):
        """
        ImageData: a class to store the data of an image
        :arg    data: the data of the image (in gray scale)
                width: the width of the image
                height: the height of the image
                fft: the FT of the image (2D FFT)
                mag: the magnitude (absolute) of fft
                magPlot: shift and log scale of mag for plotting
                phase: the phase of the fft of the image
                phasePlot: shift of phase for plotting
                real: the real component of fft
                realPlot: shift of real for plotting
                img: imaginary component of fft
                imgPlot: shift of img fot plotting
        """
        self.data = data
        self.width = width
        self.height = height
        self.fft = fft
        self.mag = mag
        self.magPlot = magPlot
        self.phase = phase
        self.phasePlot = phasePlot
        self.real = real
        self.realPlot = realPlot
        self.img = img
        self.imgPlot = imgPlot






def getImageData(path):
    """
    getImageData takes the path of the image, do the FT on it and returns arrays for its components to process on
    and plot them
    :param path: the image path
    :return: a 'ImageData' class containing the data of the image
    """

    try:
        imgData = cv2.imread(path, 0)

    except:
        return None



    fft = np.fft.fft2(imgData.data)
    fftShifted = np.fft.fftshift(fft)

    magnitudeSpectrum = np.abs(fft)
    magnitudeSpectrumPlot = (20*np.log(np.abs(fft))).astype(np.uint8)



    phaseSpectrum = np.angle(fft)
    phaseSpectrumPlot = np.angle(fftShifted)

    real = np.real(fft)
    realPlot = np.real(fftShifted)
    realPlot[realPlot<=0] = 10**-8
    realPlot = 20*np.log(realPlot)



    img = np.imag(fft)
    imgPlot = np.imag(fftShifted)
    imgPlot[imgPlot <= 0] = 10 ** -8
    imgPlot = 20*np.log(imgPlot)






    return ImageData(data=imgData,
                     width=imgData.shape[1],
                     height=imgData.shape[0],
                     fft = fft,
                     mag=magnitudeSpectrum,
                     magPlot=magnitudeSpectrumPlot,
                     phase=phaseSpectrum,
                     phasePlot=phaseSpectrumPlot,
                     real=real,
                     realPlot=realPlot,
                     img=img,
                     imgPlot=imgPlot)


def returnImage(data):
    """
    :arg data: the image 2D fft
    :return image: the image data
    """
    image = (np.fft.ifft2(data)).real
    return image


def mixArrays(comp1, comp2, comp3, comp4, sc1, sc2, mode):
    mix1 = comp1 * sc1 + comp2 * (1 - sc1)
    mix2 = comp3 * sc2 + comp4 * (1 - sc2)
    if mode == 0:
        res = np.multiply(mix1, np.exp(1j*mix2))

    elif mode == 1:
        res = mix1 + 1j * mix2

    testImage = np.abs(np.fft.ifft2(res))
    return testImage