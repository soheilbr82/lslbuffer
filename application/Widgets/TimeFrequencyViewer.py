from queue import Queue
from threading import Thread
import time
import pdb
from scipy import signal

import pyqtgraph as pg

import numpy as np
from PyQt5.QtWidgets import*
from PyQt5.QtCore import*
from PyQt5.QtGui import*

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


class SpectrumAnalyzer(QWidget):
    def __init__(self, lsl, channel):
        super(SpectrumAnalyzer, self).__init__()
        self.lsl=lsl
        self.channel = channel
        self.fs = self.lsl.get_nominal_srate()

        # self.BUFFERSIZE=2**12 #1024 is a good buffer size

        self.stop_threads = False
        self.eeg_sig = Queue()
        self.t1 = Thread(target=self.lsl.run, args=(lambda: self.stop_threads,self.eeg_sig))
        self.t1.start()
        time.sleep(1)

        self.initUI()

    
    def resetChannel(self, channel):
        if channel != self.channel:
            self.channel = channel


    def readData(self):
        sample = self.eeg_sig.get()
        shorts = sample[:, self.channel]

        return np.array(shorts)
                

    def createTimer(self):
        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self.main_loop)
        self.main_timer.start(30)


    def initUI(self):
        self.lay = QVBoxLayout()
        self.setLayout(self.lay)
        self.specWid = pg.PlotWidget(name="spectrum")
        self.specWid.setTitle("Time-Frequency Graph")
        self.specItem = self.specWid.getPlotItem()
        self.specItem.setMouseEnabled(y=False)
        self.specItem.setYRange(0, 1)
        self.specItem.setXRange(0, RANGE, padding=0)

        self.specAxis = self.specItem.getAxis("bottom")
        self.specAxis.setLabel("Frequency [Hz]")
        self.lay.addWidget(self.specWid)

        self.createTimer()

        self.show()

    #Kills thread safely
    def kill_thread(self):
        print("Killing thread....")
        self.stop_threads=True
        self.t1.join() 
        print('Thread killed.') 

    #Kills any active threads and open windows
    def close_window(self):
        self.kill_thread()
        self.main_timer.stop()
        self.close()

    def get_spectrum(self, data):
        T = 1.0 / self.fs
        N = data.shape[0]
        Pxx = (1. / N) * np.fft.fft(data)
        f = np.fft.fftfreq(N, T)
        Pxx = np.fft.fftshift(Pxx).ravel()
        f = np.fft.fftshift(f)

        return f.tolist(), (np.absolute(Pxx)).tolist()


    # Computing power spectral density using Welch's method
    def get_spectral_density(self,data):
        if(len(data) >= 2*self.fs):
            win = 2 * self.fs
            freqs, psd = signal.welch(data, self.fs, nperseg=win)
            return freqs, psd

        return (None, None)


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

    def main_loop(self):
        try:
            data = self.readData()
        except IOError:
            pass

        print(len(data))
        f, Pxx = self.get_spectral_density(data)

        if f is not None and Pxx is not None:
            self.specItem.plot(x=f, y=Pxx, clear=True)


if __name__ == '__main__':
    sa = SpectrumAnalyzer()
    sa.mainLoop()