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

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)



class EpochViewer(pg.GraphicsWindow):
    def __init__(self, lsl=None, channels=2):
        super(EpochViewer,self).__init__()
        self.resize(1000,600)
        self.setWindowTitle('pyqtgraph example: Plotting')

        self.plots = []


        streams = resolve_byprop('name', 'viz', timeout=2) # Contains information about all available lsl inlets
        if StreamInfo.name(streams[0]) == 'viz':
            self.inlet_epoch = StreamInlet(streams[0])


        self.channels = channels
        self.x = np.linspace(-0.2, 0.8,128)

        self.alphas = np.array([0.8,1, 0.2, 0.4, 0.6])
        self.linesPlotted = False
        self.epochOne=[[0 for i in range(5)] for c in range(self.channels)]
        self.epochTwo=[[0 for i in range(5)] for c in range(self.channels)]
        self.lineIndex = 0

        self.initUI()



    def createTimer(self):
        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self.main_loop)
        self.main_timer.start(30)


    def initUI(self):
        for i in range(self.channels):
            p = self.addPlot()
            self.plots.append(p)

            if i != self.channels-1:
                self.nextRow()

        self.createTimer()


    def main_loop(self):
        try:
            chunk, timestamp = self.inlet_epoch.pull_chunk()

        except IOError:
            pass

        if len(chunk) > 0:
            if self.epochOne[0].count(0) == 0 and self.epochTwo[0].count(0) == 0:
                for c in range(self.channels):
                    lineOne = self.epochOne[c][self.lineIndex]
                    lineTwo = self.epochTwo[c][self.lineIndex]
                    self.plots[c].removeItem(lineOne)
                    self.plots[c].removeItem(lineTwo)

            
            for c in range(self.channels):
                self.epochOne[c][self.lineIndex] = self.plots[c].plot(x=self.x, y=chunk[0], clear=False, pen=(0,0,255), name="Blue curve")
                self.epochTwo[c][self.lineIndex] = self.plots[c].plot(x=self.x, y=chunk[1], clear=False, pen=(255,0,0), name="Red curve")


            lineChange = [x for x in range((5-self.epochOne[0].count(0)))]
            
            if self.linesPlotted:
                for i in range(len(lineChange)):
                    for c in range(self.channels):
                        lineOne = self.epochOne[c][lineChange[i]]
                        lineTwo = self.epochTwo[c][lineChange[i]]

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