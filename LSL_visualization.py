#import lslbuffer as lb
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import lslbuffer as lb
import PyQt5
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication
import numpy as np
import pylsl
from SignalViewer import runSignal
import sys


class LSLgui():
    def __init__(self):

        #Load the UI create by Qt Creator
        self.Form, self.Window = uic.loadUiType("LSL_visualization.ui")

        
        self.lslobj = dict() #holds all of the lsl stream objects read in by lb.LSLInlets()
        self.availStrms = dict() #holds information about all of the availableStreams for the query
        self.filters=dict() #holds UI information for the various filters, i.e. notch and butter
        self.channels = [] #holds the QCheckList object for the channels for the current available stream
        self.showChnls=[]
        self.available = False
        self.current_stream_name = None
        self.streamView = False
        self.graph = None
        
        #Finds all available streams
        #If none are available, then a flag check let's the user know that none are available
        #If streams are available, then each stream is stored in an object with its metadata
        streams = pylsl.resolve_streams(wait_time=1.0)
        if len(streams) == 0:
            print("No streams available.")

        else:       
            self.available = True    
            print("Got all available streams. Starting streams now.....")        

        for s in streams:
            lsl = lb.LSLInlet(s, name=s.name())
            self.lslobj[lsl.stream_name] = lsl
            print()

    #Call this function to start the application
    def start(self):
        self.build()
        sys.exit(self.app.exec_())

    #Loads all of the available channels for the current stream under observation
    def loadChannels(self):
        self.getStreamName()
        print("Load channels for {}".format(self.current_stream_name))
        self.graph = None

        self.view.addWidget(PyQt5.QtWidgets.QCheckBox("View All Channels"))

        for index, channel in enumerate(self.lslobj[self.current_stream_name].get_channels()):
            self.channels.append(PyQt5.QtWidgets.QCheckBox("%s" % channel))
            self.view.addWidget(self.channels[index])

        self.availStrms[self.current_stream_name].clicked.connect(self.clearChannels)
        self.queryButton.clicked.connect(self.loadAvailableStreams)

    #This function is called when a different stream is chosen to view
    #Clears out the widget containing the channels from the previous stream         
    def clearChannels(self):
        self.resetStreamName()
        for i in reversed(range(self.view.count())):
            if self.view.itemAt(i).widget().isChecked():
                self.view.itemAt(i).widget().toggle()    

            self.view.itemAt(i).widget().setParent(None)
            
        self.streamClicked()
        
    #This function is called to check which available stream was chosen to view
    #Once a stream is found, it populates a widget with its available channels to view
    def streamClicked(self):
        for index, stream in enumerate(self.availStrms.keys()):
            if not self.availStrms[stream].isChecked():
                self.availStrms[stream].clicked.connect(self.loadChannels)
                break
        
    #This function is called when someone wants to populate the query with available streams
    #Populates query with stream name and the metadata for that stream, i.e. number of channels
    #sampling rate, channel format, uid, and hostname.
    def loadAvailableStreams(self):
        self.query.clear()

        if self.available != False:
            if len(self.lslobj.keys()) == 0:
                item = PyQt5.QtWidgets.QTreeWidgetItem(["No available streams of the given criteria!"])
            else:
                for index, stream in enumerate(self.lslobj.keys()):
                    self.info = self.lslobj[stream].inlet.info()
                    size = PyQt5.QtCore.QSize(100,50)
                    item = PyQt5.QtWidgets.QTreeWidgetItem(["Name: %s - Type: %s" % (stream, self.lslobj[stream].stream_type)])
                    chnlButton = PyQt5.QtWidgets.QRadioButton("View %s?" % stream)

                    self.query.addTopLevelItem(item)
                    i1 = PyQt5.QtWidgets.QTreeWidgetItem(["Channel_Count: %d" % self.info.channel_count()])
                    i2 = PyQt5.QtWidgets.QTreeWidgetItem(["Nominal_srate: %d" % self.info.nominal_srate()])
                    i3 = PyQt5.QtWidgets.QTreeWidgetItem(["Channel_format: %s" % self.info.channel_format()])
                    i4 = PyQt5.QtWidgets.QTreeWidgetItem(["uid: %s" % self.info.uid()])
                    i5 = PyQt5.QtWidgets.QTreeWidgetItem(["Hostname: %s" % self.info.hostname()])

                    item.addChild(i1)
                    item.addChild(i2)
                    item.addChild(i3)
                    item.addChild(i4)
                    item.addChild(i5)

                    self.availStrms[stream] = chnlButton
                    self.query.setItemWidget(item, 1, chnlButton)
                
                self.streamClicked()
        else:
            item = PyQt5.QtWidgets.QTreeWidgetItem([" No available streams that meet the given criteria!\n Please make sure that streams are running."])
            self.query.addTopLevelItem(item)

    #Keeps track of the current stream name
    #Will be removed in the future because it is redundant to streamClicked()
    def getStreamName(self):
        for index, stream in enumerate(self.availStrms.keys()):
            if self.availStrms[stream].isChecked():
                self.current_stream_name = stream
                break
    
    #If not stream wants to be viewed, then this function resets the current stream to None
    def resetStreamName(self):
        self.current_stream_name = None


    def loadFilters(self):
        self.filterOptions.addWidget(PyQt5.QtWidgets.QTreeWidget())
        self.filterOptions.itemAt(0).widget().setColumnCount(2)
        self.filterOptions.itemAt(0).widget().header().setSectionResizeMode(3)

        noFilter = PyQt5.QtWidgets.QTreeWidgetItem(["No Filter"])
        self.filterOptions.itemAt(0).widget().addTopLevelItem(noFilter)

        notch = PyQt5.QtWidgets.QTreeWidgetItem(["Notch Filter"])
        self.filterOptions.itemAt(0).widget().addTopLevelItem(notch)

        butter = PyQt5.QtWidgets.QTreeWidgetItem(["Butter Filter"])
        self.filterOptions.itemAt(0).widget().addTopLevelItem(butter)

        i1 = PyQt5.QtWidgets.QTreeWidgetItem(["Low Pass"])
        i2 = PyQt5.QtWidgets.QTreeWidgetItem(["High Pass"])
        butter.addChild(i1)
        butter.addChild(i2)

        lowPass = PyQt5.QtWidgets.QLineEdit()
        lowPass.setFixedHeight(30)
        lowPass.setFixedWidth(125)

        highPass = PyQt5.QtWidgets.QLineEdit()
        highPass.setFixedHeight(30)
        highPass.setFixedWidth(125)

        self.band=dict()
        self.band["low"] = lowPass
        self.band["high"] = highPass
        
        #self.filters["noFilter"]=PyQt5.QtWidgets.QRadioButton()
        #self.filters["noFilter"].click()
        #self.filters["notch"]=PyQt5.QtWidgets.QRadioButton()
        #self.filters["butter"]=PyQt5.QtWidgets.QRadioButton()

        self.filters["noFilter"]=PyQt5.QtWidgets.QCheckBox()
        self.filters["noFilter"].setChecked(True)
        self.filters["notch"]=PyQt5.QtWidgets.QCheckBox()
        self.filters["butter"]=PyQt5.QtWidgets.QCheckBox()

        self.filterOptions.itemAt(0).widget().setItemWidget(noFilter, 1, self.filters["noFilter"])
        self.filterOptions.itemAt(0).widget().setItemWidget(notch, 1, self.filters["notch"])
        self.filterOptions.itemAt(0).widget().setItemWidget(butter, 1, self.filters["butter"])
        self.filterOptions.itemAt(0).widget().setItemWidget(i1, 1, lowPass)
        self.filterOptions.itemAt(0).widget().setItemWidget(i2, 1, highPass)
        
        self.applyFilterBtn = PyQt5.QtWidgets.QPushButton("Apply Filter(s)")
        self.filterButton.addWidget(self.applyFilterBtn)
    
    def applyFilters(self):
        if self.graph:
            self.graph.applyFilter()
        else:
            print("None type object")

    def showStream(self):
        self.showChnls=[]

        if self.view.itemAt(0).widget().isChecked():
            self.showChnls = range(len(self.channels))
            print(self.showChnls)
        else:
            for index, channel in enumerate(self.channels):
                if channel.isChecked():
                    self.showChnls.append(index)
            print(self.showChnls)

        if self.graph != None:
            if self.graph.w.isActive():
                print("Active")
                self.graph.stop()
                self.graph.resetViewer(self.info.nominal_srate(), self.lslobj[self.current_stream_name].get_channels(), \
                                    self.showChnls, self.lslobj[self.current_stream_name])
                self.graph.setTimer()
        
        else:  
            self.getStreamName()
            self.loadFilters()
            self.info = self.lslobj[self.current_stream_name].inlet.info()
            self.graph = runSignal(self.info.nominal_srate(), self.lslobj[self.current_stream_name].get_channels(), \
                                self.showChnls, self.lslobj[self.current_stream_name], self.streamLabel)
            self.graph.setViewer(self.signalViewer, self.filters, self.band)
            self.graph.createTimer()
            self.graph.setTimer()
            self.visualButton.clicked.connect(self.showStream)
            self.applyFilterBtn.clicked.connect(self.applyFilters)

    #Starts/resumes the current visual of the signal viewer
    #Does not pick up from the moment it stopped, but rather the moment it would be in real-time
    def startStream(self):
        if self.graph != None:
            self.graph.start()

    #Stops the current visual of the signal viewer
    def stopStream(self):
        if self.graph != None:
            self.graph.stop()

    #Makes sure to exit the application cleanly
    def quitApp(self):
        if self.graph != None:
            self.graph.main_timer.stop()
        for key in self.lslobj.keys():
            if self.lslobj[key]:
                self.lslobj[key].disconnect()
                self.lslobj[key] = None
        self.window.close()
        self.app.quit()


    #Builds the GUI for the LSL app
    def build(self):
        self.app = QApplication([])
        self.window = self.Window()
        self.window.setWindowTitle('PyQt5 graph example: LSL GUI')
        self.form = self.Form()
        self.form.setupUi(self.window)


        self.queryButton = self.window.findChild(PyQt5.QtWidgets.QPushButton, 'queryButton')
        self.visualButton = self.window.findChild(PyQt5.QtWidgets.QPushButton, 'visualizeButton')
        self.availableStreams = self.window.findChild(PyQt5.QtWidgets.QComboBox, 'availableStreams')
        self.StreamName = self.window.findChild(PyQt5.QtWidgets.QLineEdit, 'StreamName')

        self.signalViewer = self.window.findChild(PyQt5.QtWidgets.QGridLayout, 'signalViewer')
        self.signalData = self.window.findChild(PyQt5.QtWidgets.QVBoxLayout, 'signalMetaData')
        self.stopButton = self.window.findChild(PyQt5.QtWidgets.QPushButton, 'stopStream')
        self.startButton = self.window.findChild(PyQt5.QtWidgets.QPushButton, 'startStream')
        self.quitButton = self.window.findChild(PyQt5.QtWidgets.QPushButton, 'quitButton')
        self.filterOptions = self.window.findChild(PyQt5.QtWidgets.QGridLayout, 'filtersBox')
        self.filterButton = self.window.findChild(PyQt5.QtWidgets.QGridLayout, 'applyFilter')

        self.streamData = self.window.findChild(PyQt5.QtWidgets.QVBoxLayout, 'streamData')
        self.streamLabel = self.window.findChild(PyQt5.QtWidgets.QLabel, 'streamLabel')
        self.streamLabel.setAlignment(PyQt5.QtCore.Qt.AlignCenter)
        self.streamData.addWidget(self.streamLabel)

        
        self.utkLogo = self.window.findChild(PyQt5.QtWidgets.QLabel, 'UTKlogo')
        self.utkLogo.setAlignment(PyQt5.QtCore.Qt.AlignCenter)
        self.image = PyQt5.QtGui.QPixmap("/Users/jdunkley98/Downloads/MABE-Research/lslbuffer/viz/UTKlogo.png")
        self.utkLogo.setPixmap(self.image)

        self.label = self.window.findChild(PyQt5.QtWidgets.QLabel, 'NBL')
        self.label.setAlignment(PyQt5.QtCore.Qt.AlignCenter)

        self.channelView = self.window.findChild(PyQt5.QtWidgets.QScrollArea, 'channelView')
        self.channelWidget = PyQt5.QtWidgets.QWidget()
        self.view = PyQt5.QtWidgets.QVBoxLayout()
        self.channelWidget.setLayout(self.view)
        self.channelView.setWidget(self.channelWidget)


        self.query = self.window.findChild(PyQt5.QtWidgets.QTreeWidget, 'streamMetaData')
        self.query.setColumnCount(2)
        self.query.header().setSectionResizeMode(3)


        self.queryButton.clicked.connect(self.loadAvailableStreams)
        self.visualButton.clicked.connect(self.showStream)
        self.stopButton.clicked.connect(self.stopStream)
        self.startButton.clicked.connect(self.startStream)
        self.quitButton.clicked.connect(self.quitApp)

        self.window.show()