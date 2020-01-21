from queue import Queue
from PyQt5 import QtCore, QtGui, QtWidgets
from threading import Thread

import time
import pylsl

from application.Widgets.SignalViewer import RawSignalViewer
from application.Widgets.SignalFilters import NotchFilter, ButterFilter
from application.Buffers.lslringbuffer_multithreaded import LSLRINGBUFFER

import sys
import pdb

class TimeSeriesSignal(RawSignalViewer):
    def __init__(self, fs, num_channels, showChannels, applyFilter=None, lsl_inlet=None):#lsl, view_channels=None, label1=None):
        super(TimeSeriesSignal, self).__init__(fs, num_channels, showChannels)

        self.fs = fs
        self.num_channels = num_channels
        self.showChannels = showChannels
        self.lsl_inlet = lsl_inlet

        self.filter = applyFilter
        self.Filters = {"Notch" : False, "Butter" : False}
       
        self.initUI()
        self.initFilteredGraphs()


    def createTimer(self):
        self.main_timer = QtCore.QTimer()
        self.timer = QtCore.QElapsedTimer()
        
        self.main_timer.timeout.connect(self.main_loop)
        self.main_timer.start(30)
        self.timer.start()


    def initUI(self):
        self.label1 = QtWidgets.QLabel()
        self.createTimer()
        self.show()
        

    def initFilteredGraphs(self):
        self.notch_graph = None
        self.butter_graph = None

    
    def resetChannels(self):
        pass

    
    def addFilter(self, Filter):
        if Filter == "Notch":
            self.Filters["Notch"] = True
            self.notch_graph = RawSignalViewer(self.fs, self.num_channels, self.showChannels)
            self.notch_graph.setWindowTitle('Notch Filter')
            self.notch_filter = NotchFilter(60, self.fs, len(self.num_channels))
            self.notch_graph.show()

        if Filter == "Butter":
            self.Filters["Butter"] = True
            self.butter_graph = RawSignalViewer(self.fs, self.num_channels, self.showChannels)
            self.butter_graph.setWindowTitle('Butter Filter')
            self.butter_filter = ButterFilter((0.1, (self.fs / 2) - 0.001), self.fs, len(self.num_channels))
            self.butter_graph.show()

    
    def changeFilter(self, Filter, band):
        if Filter == "Butter" and self.butter_graph is not None:
            self.butter_filter.reset(band)


    def removeFilter(self, Filter):
        if Filter == "Notch":
            self.Filters["Notch"] = False
            if self.notch_graph is not None:
                self.notch_graph.close()
                self.notch_graph = None

        if Filter == "Butter":
            self.Filters["Butter"] = False
            if self.butter_graph is not None:
                self.butter_graph.close()
                self.butter_graph = None
        
    
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


    def updateMetaData(self):
        time_elapsed = (self.timer.elapsed() / 1000)

        # Update display based on seconds, minutes, or hours ran
        if self.label1:
            if time_elapsed < 60:  # If less than a minute has gone by
                self.label1.setText(" Stream: %s\t\t Sampling rate: %d\t\t Time: %.2fs\t\t Chunk size: %d" \
                                    % (self.lsl_inlet.get_stream_name(), self.fs, self.timer.elapsed() / 1000,
                                    len(self.chunk)))
            elif time_elapsed < 3600:  # If less than an hour has gone by
                self.label1.setText(" Stream: %s\t\t Sampling rate: %d\t\t Time: %dm %.2fs\t\t Chunk size: %d" \
                                    % (
                                        self.lsl_inlet.get_stream_name(), self.fs,
                                        int((self.timer.elapsed() / 1000) / 60),
                                        (self.timer.elapsed() / 1000) % 60, len(self.chunk)))
            else:
                self.label1.setText(" Stream: %s\t\t Sampling rate: %d\t\t Time: %dh %dm %.2fs\t\t Chunk size: %d" \
                                    % (self.lsl_inlet.get_stream_name(), self.fs, int(self.timer.elapsed() / 3600),
                                    int((self.timer.elapsed() / 1000) / 60) % 60, (self.timer.elapsed() / 1000) % 60,
                                    len(self.chunk)))


    def getMetaData(self):
        return self.label1

    
    def main_loop(self):
        self.chunk, timestamp = self.lsl_inlet.get_next_chunk()
        
        if self.chunk is not None:  # Update signal and signal data if pulled chunk is not None
            self.update(self.chunk)
            self.updateMetaData()

            if any(self.Filters):

                if self.Filters["Notch"] == True:
                    self.notch_graph.update(self.notch_filter.apply(self.chunk))

                if self.Filters["Butter"] == True:
                    self.butter_graph.update(self.butter_filter.apply(self.chunk))

            
    

    def close_window(self):
        self.label1.clear()
        self.main_timer.stop()
        self.close()


if __name__ == "__main__":
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
        
        graph = TimeSeriesSignal(lsl, [0,1,2])
        graph.createTimer()
        graph.setViewer()
        graph.setTimer()
        sys.exit(graph.a.exec_())