import pdb
from queue import Queue
from threading import Thread
import time
import pdb
from scipy import signal
import spectrum

import pyqtgraph as pg
from matplotlib import pyplot

import numpy as np
from PyQt5.QtWidgets import*
from PyQt5.QtCore import*
from PyQt5.QtGui import*

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
        self.specWid.setTitle("Frequency Graph")
        self.specItem = self.specWid.getPlotItem()
        self.specItem.setMouseEnabled(y=False)
        #self.specItem.setYRange(-60, 20)
        #self.specItem.setYRange(0,1)
        self.specItem.setXRange(0, int(self.fs/2), padding=0)

        self.specAxis = self.specItem.getAxis("bottom")
        self.specAxis.setLabel("Frequency [Hz]")
        self.lay.addWidget(self.specWid)

        self.createTimer()

        self.show()

    #Kills thread 
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
        Pxx = 10*np.log10(np.absolute(Pxx))

        return f, Pxx


    # Computing power spectral density using Welch's method
    def get_welchs(self,data):
        if(len(data) >= 3*self.fs):
            win = 3 * self.fs
            freqs, psd = signal.welch(data, self.fs, nperseg=win, nfft=win, window='hanning', noverlap=win/2, scaling='density')
            psd = 10*np.log10(psd)
            return freqs, psd

        return (None, None)

    
    def get_periodograms(self, data):
        if(len(data) >= 3*self.fs):
            f, Pxx = signal.periodogram(x=data, fs=self.fs, detrend='linear')
            return f, Pxx

    def get_psd(self,data):
        if(len(data) >= 3*self.fs):
            win = 3 * self.fs
            Pxx, f = pyplot.psd(x=data, fs=self.fs, window=win, NFFT=win, detrend='linear', noverlap=win/2, scale_by_freq=True)
            Pxx = 10*np.log10(Pxx)
            return f, Pxx


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

        f, Pxx = self.get_psd(data)

        if f is not None and Pxx is not None:
            self.specItem.plot(x=f, y=Pxx, clear=True)


if __name__ == '__main__':
    sa = SpectrumAnalyzer()
    sa.mainLoop()