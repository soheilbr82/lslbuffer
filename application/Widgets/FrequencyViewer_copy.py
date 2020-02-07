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


pg.setConfigOptions(antialias=True)
class SpectrumAnalyzer(pg.PlotWidget):
    def __init__(self, lsl, channel):
        super(SpectrumAnalyzer, self).__init__()
        self.setBackgroundBrush(pg.mkBrush('#252120'))
        self.getPlotItem().setMouseEnabled(x=False)

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
        self.setTitle("Frequency Graph")
        #self.getPlotItem().setYRange(-60, 20)
        #self.specItem.setYRange(0,1)
        self.getPlotItem().setXRange(0, int(self.fs/2))

        self.specAxis = self.getPlotItem().getAxis("bottom")
        self.specAxis.setLabel("Frequency [Hz]")

        self.createTimer()


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
        #self.close()

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
            # print(psd)
            return freqs, psd

        return (None, None)

    
    def get_periodograms(self, data):
        if(len(data) >= 3*self.fs):
            print("starting periodogram")
            f, Pxx = signal.periodogram(x=data, fs=self.fs, detrend='linear')
            print("returned f and Pxx")
            Pxx = 10*np.log10(Pxx)
            print("returning...")
            return f, Pxx

        return (None, None)

    def get_psd(self,data):
        if(len(data) >= 3*self.fs):
            win = 3 * self.fs
            T = 1 / self.fs # time-step of sampling frequencies
            N = data.shape[0]

            Pxx = (np.abs(np.fft.fft(data))**2) / np.square(N)
            Pxx = 10*np.log10(Pxx)

            f = np.fft.fftfreq(data.size, T) # computes frequencies associated with FFT components
            idx = np.argsort(f) # returns a sorted array along the -1 axis
            return f[idx][int(len(f)/2):], Pxx[idx][int(len(Pxx)/2):]

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
        # pdb.set_trace()
        f, Pxx = self.get_welchs(data)

        if f is not None and Pxx is not None:
            self.getPlotItem().plot(x=f, y=Pxx, clear=True)


if __name__ == '__main__':
    sa = SpectrumAnalyzer()
    sa.mainLoop()