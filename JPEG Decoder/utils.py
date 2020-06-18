import math
from scipy.fftpack import idct
import numpy as np

def create_nd_array(shape):
    """create n-dimensional array filled with 0"""
    if len(shape) == 0: return 0
    res = []
    for _ in range(shape[0]):
        res.append(create_nd_array(shape[1:]))
    return res


def IDCT_matrix(F):
    f = np.clip(np.matrix.round(idct(idct(F, axis=0, norm='ortho'), axis=1, norm='ortho') + 128), 0, 255)
    return f


def bits_to_coefficient(bits):
    if bits[0] == 1: # positive
        return bits_to_number(bits)
    flip = [1-x for x in bits]
    return -bits_to_number(flip)

def coefficients_to_bits(val):
    if val == 0:
        return []
    elif val > 0:
        return number_to_bits(val)
    else:
        return [1-bit for bit in number_to_bits(-val)]


def number_to_bits(number):
    return [ 1 if digit == '1' else 0 for digit in bin(number)[2:]]

def bits_to_number(bits):
    """convert the binary representation to the original positive number"""
    res = 0
    for x in bits:
        res = res * 2 + x
    return res

def construct_zigzag():
    zigzag = []
    bl2tr = True # bottom-left to top-right
    for x in range(8): # first (0,0) last(7,7)   
        if bl2tr:
            for i in range(x+1):
                zigzag.append([x-i, i])
        else:
            for i in range(x+1):
                zigzag.append([i, x-i])
        bl2tr = not bl2tr
    for x in range(8, 15):
        if bl2tr:
            for i in range(x-i, 8):
                zigzag.append([x-i, i])
        else:
            for i in range(x-i, 8):
                zigzag.append([i, x-i])
        bl2tr = not bl2tr
    return zigzag

# zigzag[k] -> [i,j], k is the index in zigzag order, i, j are the indexs in the matrix
zigzag = construct_zigzag()

def zigzag2matrix(li):
    """convert a list of size 64 in zigzag order to a 8 by 8 matrix"""
    matrix = create_nd_array([8,8])
    for i, val in enumerate(li):
        x, y = zigzag[i]
        matrix[x][y] = val
    return matrix
