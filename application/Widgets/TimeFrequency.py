import pdb
from queue import Queue
from threading import Thread
import time
import pdb
from scipy import signal
import sys
import pylsl

import pyqtgraph as pg
from matplotlib import pyplot

import numpy as np
from PyQt5.QtWidgets import*
from PyQt5.QtCore import*
from PyQt5.QtGui import*
from application.Buffers.lslringbuffer_multithreaded import LSLRINGBUFFER

CHUNKZ=1024

pg.setConfigOptions(antialias=True)


class SpectrogramWidget(pg.PlotWidget):
    def __init__(self, lsl, channel, **kwargs):
        super(SpectrogramWidget, self).__init__(**kwargs)

        self.lsl=lsl
        self.channel = channel
        self.fs = self.lsl.get_nominal_srate()
        self.CHUNKSZ = self.fs*4

        self.stop_threads = False
        self.eeg_sig = Queue()
        self.t1 = Thread(target=self.lsl.run, args=(lambda: self.stop_threads,self.eeg_sig))
        self.t1.start()
        time.sleep(1)

        self.img = pg.ImageItem()
        self.addItem(self.img)

        self.initUI()

    def initUI(self):

        self.img_array = np.zeros((1000, int(self.CHUNKSZ/2+1)))

        # bipolar colormap

        pos = np.array([0., 1., 0.5, 0.25, 0.75])
        color = np.array([[0,255,255,255], [255,255,0,255], [0,0,0,255], (0, 0, 255, 255), (255, 0, 0, 255)], dtype=np.ubyte)
        cmap = pg.ColorMap(pos, color)
        lut = cmap.getLookupTable(0.0, 1.0, 256)

        self.img.setLookupTable(lut)
        self.img.setLevels([-50,40])

        freq = np.arange(int(self.CHUNKSZ/2)+1)/(float(self.CHUNKSZ)/self.fs)
        yscale = 1.0/(self.img_array.shape[1]/freq[-1])
        self.img.scale((1./self.fs)*self.CHUNKSZ, yscale)

        self.setLabel('left', 'Frequency', units='Hz')

        self.win = np.hanning(self.CHUNKSZ)
        self.show()

    def createTimer(self):
        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self.update)
        self.main_timer.start(30)

    def readData(self):
        sample = self.eeg_sig.get()
        shorts = sample[:, self.channel]

        return np.array(shorts)

    def get_welchs(self,data):
        if(len(data) >= 3*self.fs):
            win = 3 * self.fs
            freqs, psd = signal.welch(data, self.fs, nperseg=win, nfft=win, window='hanning', noverlap=win/2, scaling='density')
            psd = 10*np.log10(psd)
            # print(psd)
            return freqs, psd

        return (None, None)

    def update(self, chunk):
        # normalized, windowed frequencies in data chunk

        #spec = np.fft.rfft(chunk*self.win) / self.CHUNKSZ
        # get magnitude 

        #psd = abs(spec)
        # convert to dB scale

        #psd = 20 * np.log10(psd)

        try:
            data = self.readData()
        except IOError:
            pass

        f, Pxx = self.get_welchs(data)

        # roll down one and replace leading edge with new data

        self.img_array = np.roll(self.img_array, -1, 0)
        self.img_array[-1:] = Pxx

        self.img.setImage(self.img_array, autoLevels=False)



class TimeFrequency(QWidget):
    def __init__(self, lsl, channel, **kwargs):
        super(TimeFrequency, self).__init__(**kwargs)

        self.lsl=lsl
        self.channel = channel
        self.fs = self.lsl.get_nominal_srate()

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
        self.specWid = pg.PlotWidget(name="spectrum")
        self.specWid.setTitle("Frequency Graph")
        self.specItem = self.specWid.getPlotItem()
        self.specItem.setLabel('left', 'Frequency', units='Hz')

        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.imv1 = pg.ImageItem()
        pos = np.array([0., 1., 0.5, 0.25, 0.75])
        color = np.array([[0,255,255,255], [255,255,0,255], [0,0,0,255], (0, 0, 255, 255), (255, 0, 0, 255)], dtype=np.ubyte)
        cmap = pg.ColorMap(pos, color)
        lut = cmap.getLookupTable(0.0, 1.0, 256)

        self.imv1.setLookupTable(lut)
        self.layout.addWidget(self.imv1, 0, 0)
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


    # Computing power spectral density using Welch's method
    def get_welchs(self,data):
        if(len(data) >= 3*self.fs):
            win = 3 * self.fs
            freqs, psd = signal.welch(data, self.fs, nperseg=win, nfft=win, window='hanning', noverlap=win/2, scaling='density')
            psd = 10*np.log10(psd)
            # print(psd)
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
        # pdb.set_trace()
        f, Pxx = self.get_welchs(data)

        if f is not None and Pxx is not None:
            self.imv1.setImage(np.vstack((f, Pxx)).T)
           # ex = np.vstack((f, Pxx)).T
           # print(ex.shape)
           # print(type(ex))


if __name__ == '__main__':
    streams = pylsl.resolve_streams(wait_time=1.0)

    if len(streams) == 0:
        print("No streams available.")

    else:
        print("Got all available streams. Starting streams now.....")

       
        lsl_inlet = pylsl.StreamInlet(streams[0], max_buflen=4)
        lsl_inlet.open_stream()
        lsl = LSLRINGBUFFER(lsl_type=lsl_inlet.info().type(), name=lsl_inlet.info().name(), inlet=lsl_inlet,\
                fs=lsl_inlet.info().nominal_srate(), buffer_duration=4.0, \
                num_channels=lsl_inlet.info().channel_count(), uid=lsl_inlet.info().uid(),\
                hostname=lsl_inlet.info().hostname(), channel_format='float64')
        
        graph = TimeFrequency(lsl, [0,1,2])
        graph.createTimer()
        graph.setViewer()
        graph.setTimer()
        sys.exit(graph.a.exec_())