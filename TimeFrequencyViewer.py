import lslringbuffer_multithreaded
import lslbuffer as lb
from queue import Queue
from threading import Thread
import time
import pylsl
import pdb

import struct
import math
import sys
import numpy as np
import IPython as ipy

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore

# Audio Format (check Audio MIDI Setup if on Mac)
# FORMAT = pyaudio.paInt16
RATE = 250
CHANNELS = 32

# Set Plot Range [-RANGE,RANGE], default is nyquist/2
RANGE = None
if not RANGE:
    RANGE = RATE / 2

# Set these parameters (How much data to plot per FFT)
INPUT_BLOCK_TIME = 0.05
INPUT_FRAMES_PER_BLOCK = int(RATE * INPUT_BLOCK_TIME)

# Which Channel? (L or R)
LR = "l"


class SpectrumAnalyzer():
    def __init__(self, lsl, channel, viewer):

        self.timeFrequencyViewer = viewer
        self.lsl=lsl
        self.channel = channel

        self.stop_threads = False
        self.eeg_sig = Queue()
        self.buffer = lslringbuffer_multithreaded.LSLRINGBUFFER(lsl_type='EEG', fs=250, buffer_duration=4.0, num_channels=32)
        self.t1 = Thread(target=self.buffer.run, args=(lambda: self.stop_threads,self.eeg_sig,self.lsl,))
        self.t1.start()
        time.sleep(1)
        self.initUI()
    
    def resetChannel(self, channel):
        print("Channel reset from %d to %d" % (self.channel, channel))
        self.channel = channel

    def readData(self):
        sample = self.eeg_sig.get()
        shorts = sample[:, self.channel]

        #print(sample.shape)
        if CHANNELS == 1:
            return np.array(shorts)
        else:
            l = shorts[::2]
            r = shorts[1::2]
            if LR == 'l':
                return np.array(l)
            else:
                return np.array(r)

    def createTimer(self):
        self.main_timer = QtCore.QTimer()
        self.main_timer.timeout.connect(self.update)
        self.main_timer.start(30)

    def initUI(self):
        self.mainWindow = QtGui.QMainWindow()
        self.mainWindow.setWindowTitle("Spectrum Analyzer")
        self.mainWindow.resize(800, 300)
        self.centralWid = QtGui.QWidget()
        self.mainWindow.setCentralWidget(self.centralWid)
        self.lay = QtGui.QVBoxLayout()
        self.centralWid.setLayout(self.lay)

        self.specWid = pg.PlotWidget(name="spectrum")
        self.specItem = self.specWid.getPlotItem()
        self.specItem.setMouseEnabled(y=False)
        self.specItem.setYRange(0, 1)
        self.specItem.setXRange(0, RANGE, padding=0)

        self.specAxis = self.specItem.getAxis("bottom")
        self.specAxis.setLabel("Frequency [Hz]")
        self.lay.addWidget(self.specWid)

        self.timeFrequencyViewer.addWidget(self.mainWindow)
        self.createTimer()

        self.mainWindow.show()

    #Kills thread safely
    def kill_thread(self):
        print("Killing thread")
        self.stop_threads=True
        self.t1.join() 
        print('thread killed') 

    #Kills any active threads and open windows
    def close(self):
        self.kill_thread()
        self.main_timer.stop()
        self.mainWindow.close()

    def get_spectrum(self, data):
        T = 1.0 / RATE
        N = data.shape[0]
        Pxx = (1. / N) * np.fft.fft(data)
        f = np.fft.fftfreq(N, T)
        Pxx = np.fft.fftshift(Pxx)
        f = np.fft.fftshift(f)

        return f.tolist(), (np.absolute(Pxx)).tolist()

    # Resumes the signal viewer in real-time
    def start(self):
        if self.main_timer.isActive():
            print("timer is active")
            print("timer ID: %s" % str(self.main_timer.timerId()))
        else:
            print("timer is inactive")
            self.main_timer.start()

    # Pauses the signal viewer
    def stop(self):
        if self.main_timer.isActive():
            print("timer is active")
            print("timer ID: %s" % str(self.main_timer.timerId()))
            self.main_timer.stop()
        else:
            print("timer is inactive")

    def update(self):
        try:
            data = self.readData()
        except IOError:
            pass 
        f, Pxx = self.get_spectrum(data)
        self.specItem.plot(x=f, y=Pxx, clear=True)


if __name__ == '__main__':
    sa = SpectrumAnalyzer()
    sa.mainLoop()