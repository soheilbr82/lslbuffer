import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from queue import Queue
from threading import Thread
from scipy import signal
import time
import pylsl
from ..Buffers.lslringbuffer_multithreaded import LSLRINGBUFFER

class SpectrogramWidget(pg.PlotWidget):
    def __init__(self, lsl, channel):
        super(SpectrogramWidget, self).__init__()

        self.img = pg.ImageItem()
        self.addItem(self.img)
        self.setImg=True

        self.lsl = lsl
        self.fs = self.lsl.get_nominal_srate()
        self.channel = channel
        

        self.stop_threads = False
        self.eeg_sig = Queue()
        self.t1 = Thread(target=self.lsl.run, args=(lambda: self.stop_threads,self.eeg_sig))
        self.t1.start()
        time.sleep(1)

        self.createTimer()
        self.show()


    def createTimer(self):
        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self.update)
        self.main_timer.start(30)


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
        

    def resetChannel(self, channel):
        if channel != self.channel:
            self.channel = channel


    def readData(self):
        sample = self.eeg_sig.get()
        shorts = sample[:, self.channel]

        return np.array(shorts)
    

    def get_welchs(self,data):
        if(len(data) >= 3*self.fs):
            win = 3 * self.fs
            freqs, psd = signal.welch(data, self.fs, nperseg=win, nfft=win, window='hanning', noverlap=win/2, scaling='density')
            psd = 10*np.log10(psd)
            return freqs, psd

        return (None, None)
    

    def update(self):
        # normalized, windowed frequencies in data chunk
        try:
            data = self.readData()
            print("Length of data is: " + str(len(data)))
        except IOError:
            pass

        if(len(data) >= 3*self.fs) and self.setImg==True:
            self.img_array = np.zeros((1000, int(3*self.fs/2)+1))

            pos = np.array([0., 1., 0.5, 0.25, 0.75])
            color = np.array([[0,255,255,255], [255,255,0,255], [0,0,0,255], (0, 0, 255, 255), (255, 0, 0, 255)], dtype=np.ubyte)
            cmap = pg.ColorMap(pos, color)
            lut = cmap.getLookupTable(0.0, 1.0, 256)

            self.img.setLookupTable(lut)
            self.img.setLevels([-50,40])

            freq = np.arange(int(len(data)/2)+1)/(float(len(data))/self.fs)
            yscale = 1.0/(self.img_array.shape[1]/freq[-1])
            self.img.scale((1./self.fs)*len(data), yscale)

            self.setLabel('left', 'Frequency', units='Hz')

            self.win = np.hanning(len(data))
            self.setImg = False

 
        if(len(data) >= 3*self.fs):
            f,Pxx = self.get_welchs(data)

            if Pxx is not None:
                self.img_array = np.roll(self.img_array, -1, 0)
                self.img_array[-1:] = Pxx

                self.img.setImage(self.img_array, autoLevels=False)

