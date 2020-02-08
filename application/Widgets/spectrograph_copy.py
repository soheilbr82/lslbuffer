import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui
from queue import Queue
from threading import Thread
from scipy import signal
import time
import pylsl
from ..Buffers.lslringbuffer_multithreaded import LSLRINGBUFFER

FS = 250 #Hz

CHUNKSZ = 1024 #samples


class MicrophoneRecorder():
    def __init__(self, signal):
        self.signal = signal
        streams = pylsl.resolve_streams(wait_time=1.0)
        lsl_inlet = pylsl.StreamInlet(streams[0], max_buflen=4)
        lsl_inlet.open_stream()
        self.lsl = LSLRINGBUFFER(lsl_type=lsl_inlet.info().type(), name=lsl_inlet.info().name(), inlet=lsl_inlet,\
                fs=lsl_inlet.info().nominal_srate(), buffer_duration=4.0, \
                num_channels=lsl_inlet.info().channel_count(), uid=lsl_inlet.info().uid(),\
                hostname=lsl_inlet.info().hostname(), channel_format='float64')


        self.stop_threads = False
        self.eeg_sig = Queue()
        self.t1 = Thread(target=self.lsl.run, args=(lambda: self.stop_threads,self.eeg_sig))
        self.t1.start()
        time.sleep(1)
        #self.p = pyaudio.PyAudio()
        #self.stream = self.p.open(format=pyaudio.paInt16,
        #                    channels=1,
        #                    rate=FS,
        #                    input=True,
        #                    frames_per_buffer=CHUNKSZ)

    def readData(self):
        sample = self.eeg_sig.get()
        shorts = sample[:, 1]

        return np.array(shorts)

    def read(self):
        try:
            data = self.readData()
        except IOError:
            pass
            #y = np.fromstring(data, 'floas')
        print(len(data))
        self.signal.emit(data)
        

    def close(self):
        #self.stream.stop_stream()
        #elf.stream.close()
        #self.p.terminate()
        pass

class SpectrogramWidget(pg.PlotWidget):
    read_collected = QtCore.pyqtSignal(np.ndarray)
    def __init__(self):
        super(SpectrogramWidget, self).__init__()

        self.img = pg.ImageItem()
        self.addItem(self.img)

        self.setImg = True

        # bipolar colormap

        self.show()

    def get_welchs(self,data):
        if(len(data) >= 3*FS):
            win = 3 * FS
            freqs, psd = signal.welch(data, FS, nperseg=win, nfft=win, window='hanning', noverlap=win/2, scaling='density')
            psd = 10*np.log10(psd)
            return freqs, psd

        return (None, None)


    def update(self, chunk):
        # normalized, windowed frequencies in data chunk
        if(len(chunk) >= 3*FS) and self.setImg==True:
            self.img_array = np.zeros((1000, int(3*FS/2)+1))

            pos = np.array([0., 1., 0.5, 0.25, 0.75])
            color = np.array([[0,255,255,255], [255,255,0,255], [0,0,0,255], (0, 0, 255, 255), (255, 0, 0, 255)], dtype=np.ubyte)
            cmap = pg.ColorMap(pos, color)
            lut = cmap.getLookupTable(0.0, 1.0, 256)

            self.img.setLookupTable(lut)
            self.img.setLevels([-50,40])

            freq = np.arange(int(len(chunk)/2)+1)/(float(len(chunk))/FS)
            yscale = 1.0/(self.img_array.shape[1]/freq[-1])
            self.img.scale((1./FS)*len(chunk), yscale)

            self.setLabel('left', 'Frequency', units='Hz')

            self.win = np.hanning(len(chunk))
            self.setImg = False

            

        #spec = np.fft.rfft(chunk*self.win) / len(chunk)
        # get magnitude 

        #psd = abs(spec)
        # convert to dB scale

        #psd = 20 * np.log10(psd)
        if(len(chunk) >= 3*FS):
            f,Pxx = self.get_welchs(chunk)

            # roll down one and replace leading edge with new data

            if Pxx is not None:
                #print(len(Pxx))
                self.img_array = np.roll(self.img_array, -1, 0)
                self.img_array[-1:] = Pxx

                self.img.setImage(self.img_array, autoLevels=False)

if __name__ == '__main__':
    app = QtGui.QApplication([])
    w = SpectrogramWidget()
    w.read_collected.connect(w.update)

    mic = MicrophoneRecorder(w.read_collected)

    # time (seconds) between reads

    #interval = FS/CHUNKSZ
    t = QtCore.QTimer()
    t.timeout.connect(mic.read)
    t.start() #QTimer takes ms


    app.exec_()
    mic.close()