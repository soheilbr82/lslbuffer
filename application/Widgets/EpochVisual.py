from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from pylsl import StreamInfo, StreamInlet, resolve_byprop
import time
from PyQt5.QtWidgets import*
from PyQt5.QtCore import*
from PyQt5.QtGui import*
import pdb

app = QtGui.QApplication([])



class EpochViewer(pg.PlotWidget):
    def __init__(self, lsl=None, channel=1):
        super(EpochViewer,self).__init__()
        self.setBackgroundBrush(pg.mkBrush('#252120'))
        self.getPlotItem().setMouseEnabled(x=False)


        streams = resolve_byprop('name', 'viz', timeout=2) # Contains information about all available lsl inlets
        if StreamInfo.name(streams[0]) == 'viz':
            self.inlet_epoch = StreamInlet(streams[0])


        self.channel = channel
        self.x = np.linspace(-0.2, 0.8,128)

        self.alphas = np.array([0.8,1, 0.2, 0.4, 0.6])
        self.linesPlotted = False
        self.epochOne=[0 for i in range(5)]
        self.epochTwo=[0 for i in range(5)]
        self.lineIndex = 0

        self.initUI()



    def createTimer(self):
        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self.main_loop)
        self.main_timer.start(30)


    def initUI(self):
        self.setTitle("Frequency Graph")
        self.getPlotItem().setXRange(-0.3, 0.9)
        self.getPlotItem().setYRange(-1.5, 1.5)

        self.specAxis = self.getPlotItem().getAxis("bottom")
        self.specAxis.setLabel("Epoch Data")

        self.createTimer()


    def main_loop(self):
        try:
            chunk, timestamp = self.inlet_epoch.pull_chunk()

        except IOError:
            pass

        if len(chunk) > 0:
            if self.epochOne.count(0) == 0 and self.epochTwo.count(0) == 0:
                lineOne = self.epochOne[self.lineIndex]
                lineTwo = self.epochTwo[self.lineIndex]
                self.getPlotItem().removeItem(lineOne)
                self.getPlotItem().removeItem(lineTwo)


            self.epochOne[self.lineIndex] = self.getPlotItem().plot(x=self.x, y=chunk[0], clear=False, pen=(0,0,255), name="Blue curve")
            self.epochTwo[self.lineIndex] = self.getPlotItem().plot(x=self.x, y=chunk[1], clear=False, pen=(255,0,0), name="Red curve")

            lineChange = [x for x in range((5-self.epochOne.count(0)))]# if x != self.lineIndex]
            
            if self.linesPlotted:
                for i in range(len(lineChange)):
                    lineOne = self.epochOne[lineChange[i]]
                    lineTwo = self.epochTwo[lineChange[i]]

                    lineOne.setAlpha(self.alphas[i], False)
                    lineTwo.setAlpha(self.alphas[i], False)

                self.alphas = np.roll(self.alphas, 1)

            else:
                self.linesPlotted = True

            if self.lineIndex < 4:
                self.lineIndex += 1
            else:
                self.lineIndex = 0


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        o = EpochViewer()
        o.show()
        QtGui.QApplication.instance().exec_()
        sys.exit(1)