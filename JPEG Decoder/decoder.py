from marker import *
from huffman import create_huffman_tree
import numpy as np
from utils import *
from PIL import Image
import time
import math
from stream import Stream
from component import Component
import copy
import matplotlib.pyplot as plt
import os
from io import BytesIO
from PyQt5.QtWidgets import QApplication

class Decoder:
    def __init__(self, filename, text):
        self.filename = filename
        self.text = text
        self.buffer = open(filename, 'rb').read()
        print(self.buffer)
        self.pos = 0
        self.quantizationTables = {}    # (quantizationID: quantizationTable)
        self.DCHuffman = {}             # (DCHuffmanID: DCHuffmanTree)
        self.ACHuffman = {}             # (ACHuffmanID: ACHuffmanTree)
        self.components = {}            # (ComponentID: Component)
        self.dataList = []              # [Scan0, Scan1, Scan2, ......]
        self.string = 0                 # A String used to store the scanned data into an image
        self.images = []                # A list of PIL image scans data
        self.mode = None                # Mode: SF02 For progressive
        self.height = 0                 # Height of Image
        self.width = 0                  # Width of Image
        self.MCUWidth = 0               # Width of Minimum-Coded-Unit (MCU)
        self.MCUHeight = 0              # Height of Minimum-Coded-Unit (MCU)
        self.VMCUNo = 0                 # No. of MCUs in the vertical axis
        self.HMCUNo = 0                 # No. of MCUs in the horizontal axis
        self.stuffedHeight = 0          # A variable used to make sure that the pixels in vertical axis are suitable to build integer no. of MCUs
        self.stuffedWidth = 0           # A variable used to make sure that the pixels in horizontals axis are suitable to build integer no. of MCUs
        self.scan = 0                   # No. of scans in the JPG image (usually 8-11) in progressive JPEGs
        self.stream = None              # A stream object from stream.py to read the bytes when reading the frames
        self.data = None                # a variable used to store the decoded image data for each scan and store it as image

    def StreamInit(self):
        """
        StreamInit creates a Stream object and looping on the data buffer until reaching a non-padding character,
        in each step of the loop the stream object writes the character in the stream
        """
        stream = Stream()
        while True:
            char = self.readByte()
            if char != 0xff:
                stream.write_byte(char)
            else:
                padding = self.readByte()
                if padding == 0x00:     # remove byte padding 0x00
                    stream.write_byte(char)
                else:                   # char is the first byte of the next marker
                    self.pos -= 2
                    break
        self.stream = stream

    
    def readNBits(self, N, extend=True):
        """
        readNBits: read a number N of bits of the data buffer
        :param N: the number of bits to be read
        :param extend: if extend: tthe bis are repersented in coef format otherwise are numbers
        :return: the coef(if extend) or number (if not extend)
        """
        if N == 0: return 0
        bits = []
        for _ in range(N):
            bits.append(self.stream.read_bit())
        if extend:
            return bits_to_coefficient(bits)
        else:
            return bits_to_number(bits)

    def readFourBits(self):
        """
        readFourBitss: read a byte and return the 4 most significant bits and the 4 least significant bits
        :return: a tuple of the decimal of the 2 4-bits divided byte
        """
        val = self.readByte()
        print("Val-4Bit: ", val >> 4, "Val-4Bit: ", val % (2**4))
        return val >> 4, val % (2 ** 4)

    def readByte(self):
        """
        readByte: read a byte of the buffer by accessing the buffer list by index of self.pos
        :return: the value of the self.pos th element of the buffer list
        """
        self.pos += 1
        return self.buffer[self.pos - 1]

    def readByteNoneInc(self):
        """
        readByteNoneInc: read a byte of the buffer by accessing the buffer list by index of self.pos without increment of self.pos
        :return: the value of the self.pos th element of the buffer list
        """
        return self.buffer[self.pos]

    def readTwoBytes(self):
        """
        readTwoBytes: read two bytes in row
        :return: the decimal of the two bytes after combining them together
        """
        h, l = self.readByte(), self.readByte()
        print("h: ", h, " l: ", l, " pos: ", self.pos)
        return h * 256 + l

    def readHuffmanSymbol(self, ht):
        """
        readHuffmanSymbol: read bits from the stream and decode them according to Huffman table
        :return: symbol: a Huffman-encoded symbol
        """
        while True:
            symbol = ht.get_bit(self.stream.read_bit())
            if symbol != None:
                return symbol



    def run(self):
        """
        run: looping on the markers set by markers in marker_dict in marker.py and calling different functions
             according to each marker
        """
        self.pos = 0
        while True:
            val = self.readByte()
            if val == 0xff:
                marker_type = self.readByte()
                print("I am marker {} at index {}".format(hex(self.buffer[self.pos-1]), self.pos-1))
                if marker_type in marker_dict:
                    if marker_type == EOI:
                        break
                    elif marker_type == SOI:
                        continue
                    elif marker_type == DHT:
                        self.readHuffmanTable()
                    elif marker_type == DQT:
                        self.readQT()
                    elif marker_type == SOF0 or marker_type == SOF2:
                        self.readFrame(mode=marker_type)
                    elif marker_type == SOS:
                        self.ReadScan()
                        self.scan += 1
                        if self.mode == SOF0:
                            break
                    elif marker_type == APP0 or marker_type == APP1:
                        length = self.readTwoBytes()
                        self.pos += length - 2
                        print(length)
                else:
                    print(hex(marker_type))
        print("Mode: ----> ", marker_dict[self.mode])

    def decodeComponents(self, i):
        """
        decodeComponents: taking read info of the jepg and applying the steps of converting this data into image data
        :param i: the index of the component [scan] to be decoded
        """
        if i > 7:
            dataIndex = 7
        else:
            dataIndex = i
        components = self.dataList[i]
        self.reverseQT(components)
        self.text.append("Reverse Qunatization Table is done for scan {}".format(dataIndex+1))
        QApplication.processEvents()
        self.reverseZigZag(components)
        self.text.append("Reverse ZigZag is done for scan {}".format(dataIndex+1))
        self.text.append("IDCT for scan {} statred. It takes some time.".format(dataIndex+1))
        QApplication.processEvents()
        self.reverseDCT(components)
        self.text.append("IDCT is done for scan {}".format(dataIndex+1))
        QApplication.processEvents()
        self.reverseSplitBlock(components)
        self.text.append("Reverse Split Block is done for scan {}".format(dataIndex+1))
        QApplication.processEvents()
        newpath = self.save()
        return newpath

    def readFrame(self, mode):
        """
        readFrame: reading important information about the image regarding its mode, the frequency and precision of each
                   component
        :param mode: BASELINE/PROGRESSIVE
        """
        length = self.readTwoBytes()
        self.mode = mode
        sample_precision = self.readByte() # almost always be 8
        height = self.readTwoBytes()
        width = self.readTwoBytes()
        self.height, self.width = height, width
        nr_components = self.readByte() # 3 for YCbCr or 1 for Y(grayscale)
        print(f"SOF, sample precision: {sample_precision}, height: {height}, width: {width}, number of components: {nr_components}")
        max_hf, max_vf = 1, 1
        for _ in range(nr_components):
            component_id = self.readByte()
            hf, vf = self.readFourBits()
            print(hf, vf)
            if hf > max_hf: max_hf = hf
            if vf > max_vf: max_vf = vf
            qt_selector = self.readByte()
            print(f"component_id: {component_id}, horizontal and vertical"
             f"sampling frequencies: {hf}-{vf}, qt selector: {qt_selector}")
            self.components[component_id] = Component(hf, vf, self.quantizationTables[qt_selector], component_id)
       
        self.MCUWidth = 8 * max_hf
        self.MCUHeight = 8 * max_hf
        self.VMCUNo = math.ceil(height / self.MCUHeight)
        self.HMCUNo = math.ceil(width / self.MCUWidth)
        self.stuffedHeight = self.MCUHeight * self.VMCUNo
        self.stuffedWidth = self.MCUWidth * self.HMCUNo
        for cp in self.components.values():
            cp.block_height = 8 * max_vf // cp.vf
            cp.block_width = 8 * max_hf // cp.hf
            cp.nr_blocks_ver = math.ceil(self.height/cp.block_height)
            cp.nr_blocks_hor = math.ceil(self.width/cp.block_width)
            cp.blocks = create_nd_array([self.stuffedHeight//cp.block_height, self.stuffedWidth//cp.block_width,64])

    def readHuffmanTable(self):
        """
        readHuffmanTable: reading after reaching huffman marker each component's huffman tree of each value and code
                          representation
        """
        length = self.readTwoBytes()
        # there can be multiple Huffman tables, so we loop until a 0xff indicates a new marker
        while self.readByteNoneInc() != 0xff:
            table_class, ht_identifier = self.readFourBits()
            print(f"DHT, Huffman table: {ht_identifier}, for", ("AC" if table_class else "DC"))
            bits = []
            for _ in range(16):
                bits.append(self.readByte())
            nr_codewords = sum(bits)
            huffvals = []
            for _ in range(nr_codewords):
                huffvals.append(self.readByte())
            huffman_tree = create_huffman_tree(bits, huffvals)
            if table_class == 1:
                self.ACHuffman[ht_identifier] = huffman_tree
            else:
                self.DCHuffman[ht_identifier] = huffman_tree
            huffman_tree.print_tree()

    def readQT(self):
        """
        readQT: reading the quantization table of each component
        """
        print("I am at index {} and value {}".format(self.pos, self.buffer[self.pos]))
        length = self.readTwoBytes()
        # there can be multiple quantization tables, so we loop until a 0xff indicates a new marker
        while self.readByteNoneInc() != 0xff:
            precision, identifier = self.readFourBits()
            print(f"DQT, quantization table precision: {precision}, identifier: {identifier}")
            # precision 0 for 8 bit, 1 for 16 bit
            if precision == 0:
                qt = []
                for _ in range(64):
                    qt.append(self.readByte())
                print(qt)
                print(len(qt))
                self.quantizationTables[identifier] = qt
            elif precision == 1:
                qt = []
                for _ in range(64):
                    qt.append(self.readTwoBytes())
                print(qt)
                self.quantizationTables[identifier] = qt

    def ReadScan(self):
        """
        ReadScan: reading the data of each scan of the jpeg image and store the data scanned of each component in the
                  components dictionary and the dataList
        """
        length = self.readTwoBytes()
        nr_components = self.readByte()
        print(f"SOS, number of components in a scan: {nr_components}")
        interleaved_components = []
        for _ in range(nr_components):
            component_selector = self.readByte()
            DCht_selector, ACht_selector = self.readFourBits()
            cp = self.components[component_selector]
            cp.DCht = self.DCHuffman[DCht_selector] if DCht_selector in self.DCHuffman else None
            cp.ACht = self.ACHuffman[ACht_selector] if ACht_selector in self.ACHuffman else None
            interleaved_components.append(cp)
            print(f"component selector: {component_selector}, DC/AC huffman table {DCht_selector} {ACht_selector}")
        Ss = self.readByte()
        Se = self.readByte()
        Ah, Al = self.readFourBits()
        print(f"(Ss, Se) = {Ss}, {Se}, (Ah, Al) = {Ah}, {Al}")
        self.StreamInit()
        if self.mode == SOF0: # sequential
            return
        elif self.mode == SOF2: # progressive
            if Ss == 0:
                if Ah == 0: # DC first scan
                    self.decode_DC_progressive_first(interleaved_components, Al)
                else: # DC subsequent scan
                    self.decode_DC_progressive_subsequent(interleaved_components, Al)
            elif Ah == 0: # AC first scan
                self.decode_ACs_progressive_first(interleaved_components, Ss, Se, Al)
            else: # AC subsequent scan
                self.decode_ACs_progressive_subsequent(interleaved_components, Ss, Se, Al)
        comp = copy.deepcopy(self.components)
        self.dataList.append(comp)


    def decode_DC_progressive_first(self, interleaved_components, Al):
        """DC can be interleaved"""
        for cp in interleaved_components: cp.prev_DC = 0
        for i in range(self.VMCUNo):
            for j in range(self.HMCUNo):
                for cp in interleaved_components:
                    v_idx, h_idx = cp.vf * i, cp.hf * j # top-left block
                    for m in range(cp.vf):
                        for n in range(cp.hf):
                            block = cp.blocks[v_idx+m][h_idx+n]
                            cp.prev_DC = self.decode_DC_progressive_first_per_block(cp.DCht, block, Al, cp.prev_DC)

    def decode_DC_progressive_first_per_block(self, DCht, block, Al, prev_DC):
        DC_size = self.readHuffmanSymbol(DCht)
        newDC = self.readNBits(DC_size) + prev_DC
        block[0] = newDC << Al
        return newDC
        
    def decode_DC_progressive_subsequent(self, interleaved_components, Al):
        for i in range(self.VMCUNo):
            for j in range(self.HMCUNo):
                for cp in interleaved_components:
                    v_idx, h_idx = cp.vf * i, cp.hf * j # top-left block
                    for m in range(cp.vf):
                        for n in range(cp.hf):
                            block = cp.blocks[v_idx+m][h_idx+n]
                            self.decode_DC_progressive_subsequent_per_block(block, Al)

    def decode_DC_progressive_subsequent_per_block(self, block, Al):
        bit = self.stream.read_bit()
        block[0] |= bit << Al

    def decode_ACs_progressive_first(self, interleaved_components, Ss, Se, Al):
        """must be non-interleaved"""
        cp = interleaved_components[0]
        length_EOB_run = 0
        for i in range(cp.nr_blocks_ver):
            for j in range(cp.nr_blocks_hor):
                block = cp.blocks[i][j]
                length_EOB_run = self.decode_ACs_progressive_first_per_block(cp.ACht, block, Ss, Se, Al, length_EOB_run)

    def decode_ACs_progressive_first_per_block(self, ACht, block, Ss, Se, Al, length_EOB_run):
        """the first scan of successive approximation or spectral selection only"""
        # this is a EOB
        if length_EOB_run > 0:
            return length_EOB_run - 1

        idx = Ss
        while idx <= Se:
            symbol = self.readHuffmanSymbol(ACht)
            RUNLENGTH, SIZE = symbol >> 4, symbol % (2**4)

            if SIZE == 0:
                if RUNLENGTH == 15: # ZRL(15,0)
                    idx += 16
                else: # EOBn, n=0-14
                    return self.readNBits(RUNLENGTH, False) + (2**RUNLENGTH) - 1
            else:
                idx += RUNLENGTH
                block[idx] = self.readNBits(SIZE) << Al
                idx += 1
        return 0

    def decode_ACs_progressive_subsequent(self, interleaved_components, Ss, Se, Al):
        cp = interleaved_components[0]
        length_EOB_run = 0
        for i in range(self.VMCUNo):
            for j in range(self.HMCUNo):
                block = cp.blocks[i][j]
                length_EOB_run = self.decode_ACs_progressive_subsequent_per_block(cp.ACht, block, Ss, Se, Al, length_EOB_run)

    def decode_ACs_progressive_subsequent_per_block(self, ACht, block, Ss, Se, Al, length_EOB_run):
        idx = Ss
        # this is a EOB
        if length_EOB_run > 0:
            while idx <= Se:
                if block[idx] != 0:
                    self.refineAC(block, idx, Al)
                idx += 1
            return length_EOB_run - 1

        while idx <= Se:
            symbol = self.readHuffmanSymbol(ACht)
            RUNLENGTH, SIZE = symbol >> 4, symbol % (2**4)
            if SIZE == 1: # zero history
                val = self.readNBits(SIZE) << Al
                while RUNLENGTH > 0 or block[idx] != 0:
                    if block[idx] != 0:
                        self.refineAC(block, idx, Al)
                    else:
                        RUNLENGTH -= 1
                    idx += 1
                block[idx] = val
                idx += 1
            elif SIZE == 0:
                if RUNLENGTH < 15: # EOBn, n=0-14 
                    # !!! read EOB run first
                    newEOBrun = self.readNBits(RUNLENGTH, False) + (1<<RUNLENGTH)
                    while idx <= Se:
                        if block[idx] != 0:
                            self.refineAC(block, idx, Al)
                        idx += 1
                    return newEOBrun - 1
                else: # ZRL(15,0)
                    while RUNLENGTH >= 0:
                        if block[idx] != 0:
                            self.refineAC(block, idx, Al)
                        else:
                            RUNLENGTH -= 1
                        idx += 1
        return 0

    def refineAC(self, block, idx, Al):
        val = block[idx]
        if val > 0:
            if self.stream.read_bit() == 1:
                block[idx] += 1 << Al
        elif val < 0:
            if self.stream.read_bit() == 1:
                block[idx] += (-1) << Al
            

    def reverseQT(self, components):
        for cp in components.values():
            for i in range(cp.nr_blocks_ver):
                for j in range(cp.nr_blocks_hor):
                    for k in range(64):
                        cp.blocks[i][j][k] *= cp.qt[k]


    def reverseZigZag(self, components):
        for cp in components.values():
            for i in range(self.stuffedHeight // cp.block_height):
                for j in range(self.stuffedWidth // cp.block_width):
                    cp.blocks[i][j] = zigzag2matrix(cp.blocks[i][j])

    def reverseDCT(self, components):
        """cost the most time"""
        for cp in components.values():
            for i in range(cp.nr_blocks_ver):
                for j in range(cp.nr_blocks_hor):
                    cp.blocks[i][j] = IDCT_matrix(cp.blocks[i][j])

    def reverseSplitBlock(self, components):
        pixels = create_nd_array([self.stuffedHeight, self.stuffedWidth, 3])
        cp_idx = 0
        for cp in components.values():
            for i in range(self.VMCUNo):
                for j in range(self.HMCUNo):
                    for u in range(cp.vf):
                        for v in range(cp.hf):
                            block = cp.blocks[i*cp.vf+u][j*cp.hf+v]
                            # (v_idx, h_idx) top-left corner of pixel block
                            v_idx = i * self.MCUHeight + u * cp.block_height
                            h_idx = j * self.MCUWidth + v * cp.block_width
                            step_r, step_c = cp.block_height // 8, cp.block_width // 8
                            for m in range(8):
                                for n in range(8):
                                    val = block[m][n]
                                    for x in range(step_r):
                                        for y in range(step_c):
                                            pixels[v_idx+m*step_r+x][h_idx+n*step_c+y][cp_idx] = val
            cp_idx += 1
        self.data = pixels


    
    def save(self):
        array = np.array(self.data, dtype=np.uint8)
        new_image = Image.fromarray(array, 'YCbCr')
        newPath = "OP/new" + str(self.string)+ ".JPG"
        new_image.crop((0,0,self.width,self.height)).save(newPath)
        self.images.append(newPath)
        self.string += 1
        return newPath



