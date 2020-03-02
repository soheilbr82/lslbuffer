from pyqtgraph.Qt import QtGui, QtCore
from PyQt5.QtWidgets import*
from PyQt5.QtCore import*
from PyQt5.QtGui import*
import numpy as np
import pyqtgraph as pg
from pylsl import StreamInfo, StreamInlet, resolve_byprop
import pdb

app = QtGui.QApplication([])

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)


class EpochViewer(pg.GraphicsWindow):
    def __init__(self, lsl=None, channels=1):
        super(EpochViewer,self).__init__()
        self.resize(1200,1000)
        self.setWindowTitle('Epoch Viewer')
        self.monitor = QDesktopWidget().screenGeometry(0)
        self.move(self.monitor.left(), self.monitor.top())

        self.plots = []


        streams = resolve_byprop('name', 'viz', timeout=2) # Contains information about all available lsl inlets
        if StreamInfo.name(streams[0]) == 'viz':
            self.inlet_epoch = StreamInlet(streams[0])


        self.channels = channels
        self.x = np.linspace(-0.2, 0.8,128)

        self.epochOneAlphas = np.array([0.8,1, 0.2, 0.4, 0.6])
        self.epochTwoAlphas = np.array([0.8,1, 0.2, 0.4, 0.6])
        self.linesPlotted = False
        self.epochOne=[[0 for i in range(5)] for c in range(self.channels)]
        self.epochTwo=[[0 for i in range(5)] for c in range(self.channels)]
        self.epochOneIndex = 0
        self.epochTwoIndex = 0

        self.initUI()



    def createTimer(self):
        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self.main_loop)
        self.main_timer.start(30)


    def initUI(self):
        for i in range(self.channels):
            p = self.addPlot(title="Channel %s" % str(i+1))
            self.plots.append(p)

            if i % 2:
                self.nextRow()

        self.createTimer()


    def main_loop(self):
        try:
            chunk, timestamp = self.inlet_epoch.pull_chunk(timeout=0.01)

        except IOError:
            pass

        if len(chunk) > 0:
            chunk = np.asarray(chunk)
            lineChange = []

            if self.epochOne[0].count(0) == 0:
                for c in range(self.channels):
                    if chunk[-1][0] == 1:
                        lineOne = self.epochOne[c][self.epochOneIndex]
                        self.plots[c].removeItem(lineOne)

            if self.epochTwo[0].count(0) == 0:
                for c in range(self.channels):
                    if chunk[-1][0] == -1:
                        lineTwo = self.epochTwo[c][self.epochTwoIndex]
                        self.plots[c].removeItem(lineTwo)

            
            for c in range(self.channels):
                if chunk[-1][0] == 1:
                    self.epochOne[c][self.epochOneIndex] = self.plots[c].plot(x=self.x, y=chunk[c,:], clear=False, pen=(0,0,255), name="Blue curve")
                elif chunk[-1][0] == -1:    
                    self.epochTwo[c][self.epochTwoIndex] = self.plots[c].plot(x=self.x, y=chunk[c,:], clear=False, pen=(255,0,0), name="Red curve")

            if chunk[-1][0] == 1:
                lineChange = [x for x in range((5-self.epochOne[0].count(0)))]
            elif chunk[-1][0] == -1:
                lineChange = [x for x in range((5-self.epochTwo[0].count(0)))]
            
            if self.linesPlotted:
                for i in range(len(lineChange)):
                    for c in range(self.channels):
                        if chunk[-1][0] == 1:
                            lineOne = self.epochOne[c][lineChange[i]]
                            lineOne.setAlpha(self.epochOneAlphas[i], False)
                           

                        elif chunk[-1][0] == -1:
                            lineTwo = self.epochTwo[c][lineChange[i]]
                            lineTwo.setAlpha(self.epochTwoAlphas[i], False)

                if chunk[-1][0] == 1:
                    self.epochOneAlphaslphas = np.roll(self.epochOneAlphas, 1)
                elif chunk[-1][0] == -1:
                    self.epochTwoAlphaslphas = np.roll(self.epochTwoAlphas, 1)

            else:
                self.linesPlotted = True

            if chunk[-1][0] == 1:
                if self.epochOneIndex < 4:
                    self.epochOneIndex += 1
                else:
                    self.epochOneIndex = 0
            elif chunk[-1][0] == -1:
                if self.epochTwoIndex < 4:
                    self.epochTwoIndex += 1
                else:
                    self.epochTwoIndex = 0


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        if len(sys.argv) > 1:
            o = EpochViewer(channels=int(sys.argv[1]))
        else:
            o = EpochViewer()
        sa = pg.QtGui.QScrollArea() 
        sa.setWidget(o)
        o.show()
        sa.show()
        QtGui.QApplication.instance().exec_()
        sys.exit(1)