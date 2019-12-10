from SignalViewer import RawSignalViewer
from SignalFilters import *
from queue import Queue
from PyQt5 import QtCore, QtGui, QtWidgets



class runSignal:
    def __init__(self, fs, n_channels, view_channels, lsl, label1):
        self.fs = fs
        self.sec_to_plot = 10
        self.n_samples = self.sec_to_plot * self.fs
        self.n_channels = n_channels
        self.view_channels = view_channels
        self.chunk_len = 8       
        self.chunk = None
        self.length_of_chunk = 0

        self.lsl = lsl #Holds current stream object
        self.label1 = label1 #Widget that contains real-time stream metadata
        self.notch_filter=None
        self.butter_filter=None
        self.apply_filters = False #Checks to see if filters are wanting to be applied by the user
        self.q = Queue() #buffer for real-time data -> tracks last 4 seconds of data
        
        
    #Sets the graph of the signal viewer
    def setViewer(self, layout1, filters=None, band=None):
        self.w = RawSignalViewer(self.fs, self.n_channels, self.view_channels)
        self.layout1=layout1
        self.layout1.addWidget(self.w)
        self.w.show()

        if filters and band:
            print("Band and Filters is not None")
            self.filters = filters
            self.band = band
            self.band["low"].setPlaceholderText("Minimum: 0.1")
            self.band["high"].setPlaceholderText("Maximum: %.3f" % float(self.fs/2-.001))
            self.low = None
            self.high = None
            self.w2 = RawSignalViewer(self.fs, self.n_channels, self.view_channels)
            self.w3 = RawSignalViewer(self.fs, self.n_channels, self.view_channels)
        
        self.timer = QtCore.QElapsedTimer()
        self.time = 0

    #Reset the signal viewer graph if new channels are selected
    #Clears out widgets of previous signal objects and then resets the new signal object with the new list of channels
    def resetViewer(self, fs, n_channels, view_channels, lsl):
        self.fs = fs
        self.n_channels = n_channels
        self.view_channels = view_channels
        self.lsl = lsl

        self.w.close()
        self.layout1.removeWidget(self.w)
        del self.w

        if self.w2.isVisible():
            self.w2.close()
            del self.w2
            self.w2 = RawSignalViewer(self.fs, self.n_channels, self.view_channels)
        if self.w3.isVisible():
            self.w3.close()
            del self.w3
            self.w3 = RawSignalViewer(self.fs, self.n_channels, self.view_channels)

        self.setViewer(self.layout1)

    def createTimer(self):
        self.main_timer = QtCore.QTimer()

    #sets the application timer for the signal viewer
    #Also sets a clock timer to track how long the signal has been viewed in real-time
    def setTimer(self):
        self.label1.setText("Getting Stream Data......")
        self.main_timer.timeout.connect(self.update)
        self.main_timer.start(30)
        self.timer.start()

    #Resumes the signal viewer in real-time
    def start(self):
        if self.main_timer.isActive() == True:
            print("timer is active")
            print("timer ID: %s" % str(self.main_timer.timerId()))
        else:
            print("timer is inactive")
            self.main_timer.start()

    #Pauses the signal viewer
    def stop(self):
        if self.main_timer.isActive() == True:
            print("timer is active")
            print("timer ID: %s" % str(self.main_timer.timerId()))
            self.main_timer.stop()
        else:
            print("timer is inactive")
    
    def updateData(self):
        time_elapsed = (self.timer.elapsed()/1000)

        #Create a buffer of the last four seconds of data acquired
        #Time buffer can be adjusted based on the amount of seconds of data needed
        if time_elapsed <= 4:
            self.q.put(self.chunk)
        else:
            self.q.get()
            self.q.put(self.chunk)
  
        #Update display based on seconds, minutes, or hours ran
        if time_elapsed < 60: #If less than a minute has gone by
            self.label1.setText(" Stream: %s\t\t Sampling rate: %d\t\t Time: %.2fs\t\t Chunk size: %d" \
                %(self.lsl.stream_name, self.lsl.get_frequency(), self.timer.elapsed()/1000, len(self.chunk)))
        elif time_elapsed < 3600:#If less than an hour has gone by
            self.label1.setText(" Stream: %s\t\t Sampling rate: %d\t\t Time: %dm %.2fs\t\t Chunk size: %d" \
                %(self.lsl.stream_name, self.lsl.get_frequency(), int((self.timer.elapsed()/1000)/60), \
                    (self.timer.elapsed()/1000)%60, len(self.chunk)))
        else:
            self.label1.setText(" Stream: %s\t\t Sampling rate: %d\t\t Time: %dh %dm %.2fs\t\t Chunk size: %d" \
                %(self.lsl.stream_name, self.lsl.get_frequency(), int(self.timer.elapsed()/3600), \
                    int((self.timer.elapsed()/1000)/60)%60 , (self.timer.elapsed()/1000)%60, len(self.chunk)))

    #Defines low band pass
    def lowPass(self):
        if len(self.band["low"].text()) == 0:
            self.low = None
        else:
            if 0.1 <= float(self.band["low"].text()):
                self.low = float(self.band["low"].text())
                print(self.low)

    #Defines high band pass
    def highPass(self):
        if len(self.band["high"].text()) == 0:
            self.high = None
        else:
            if float(self.band["high"].text()) < self.fs/2:
                self.high = float(self.band["high"].text())
            

    #Applies filters to real-time EEG data
    #Windows for each filter will appear when button is clicked
    #Window will not disappear unless another filter or no filter is specified and 

    def removeFilter(self):
            if self.w2.isVisible():
                    self.w2.close()
            if self.w3.isVisible():
                    self.w3.close()

            if self.apply_filters == True:
                self.apply_filters = False

    def applyFilter(self):
        #Generates a new window of signal data per filter desired
            if self.filters["notch"].isChecked():
                if self.apply_filters == False:
                    self.apply_filters = True

                if self.w2.isVisible():
                    pass
                else:
                    print("Notch")
                    self.w2.show()
                    self.w2.setWindowTitle("Notch Filter")

                self.notch_filter = NotchFilter(60, self.fs, len(self.n_channels))
                self.w2.update(self.notch_filter.apply(self.chunk))
            if self.filters["butter"].isChecked():
                if self.apply_filters == False:
                    self.apply_filters = True

                if self.w3.isVisible():
                    pass
                else:
                    print("Butter")
                    self.w3.show()
                    self.w3.setWindowTitle("Butter Filter")

                self.band["low"].editingFinished.connect(self.lowPass)
                self.band["high"].editingFinished.connect(self.highPass)
    
                if self.low or self.high:
                    self.butter_filter = ButterFilter((self.low, self.high), self.fs, len(self.n_channels))
                elif self.low == None and self.high == None:
                    self.butter_filter = ButterFilter((0.1, (self.fs/2)-0.001), self.fs, len(self.n_channels))

                self.w3.update(self.butter_filter.apply(self.chunk))


    def update(self):
        self.time += self.chunk_len
        self.chunk, timestamp = self.lsl.get_next_chunk()
        
        if self.chunk is not None: #Update signal and signal data if pulled chunk is not None
            self.w.update(self.chunk)
            if self.apply_filters == True:
                self.applyFilter()
            else:
                pass
            self.updateData()