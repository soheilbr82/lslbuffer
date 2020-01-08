#PyQt5 modules
from PyQt5 import uic
from PyQt5.QtWidgets import*
from PyQt5.QtCore import*
from PyQt5.QtGui import*
import pyqtgraph as pg

#Self created modules
from Widgets.Logo import UTKLogo
from Widgets.Error import ErrorBox
from Widgets.TimeFrequencyViewer import SpectrumAnalyzer
from Widgets.TimeSeriesViewer import TimeSeriesSignal
from Buffers.lslringbuffer_multithreaded import LSLRINGBUFFER

#Python library modules
import pylsl
import sys

class LSLgui(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(LSLgui, self).__init__(*args, **kwargs)

        uic.loadUi("Revisions/Visuals/LSL_visualization.ui", self) # Load the .ui file
        self.setWindowTitle('LSL Real-Time Analysis')   
        self.setMaximumSize(1150,1000) 

        self.avail_streams = dict()  # holds information about all of the availableStreams for the query
        self.filters = {"Notch": False, "Butter": False}  # holds UI information for the various filters, i.e. notch and butter
        self.lslobj = dict()

        self.channels = []  # holds the QCheckList object for the channels for the current available stream
        self.showChannels = []  # holds the channels selected for visualization

        self.currentStreamName = None  # holds the current stream name of the stream wanting to be observed
        self.streamView = None
        self.graph = None

        self.initUI() 


    def getAvailableStreams(self):
        self.isAvailable = False
        self.lslobj.clear()

        streams = pylsl.resolve_streams(wait_time=1.0)

        if len(streams) == 0:
            print("No streams available.")
            self.clearChannels()

        else:
            self.isAvailable = True
            print("Got all available streams. Starting streams now.....")

            for s in streams:
                lsl_inlet = pylsl.StreamInlet(s, max_buflen=4)
                lsl_inlet.open_stream()
                lsl = LSLRINGBUFFER(lsl_type=lsl_inlet.info().type(), name=lsl_inlet.info().name(), inlet=lsl_inlet,\
                        fs=lsl_inlet.info().nominal_srate(), buffer_duration=4.0, \
                        num_channels=lsl_inlet.info().channel_count(), uid=lsl_inlet.info().uid(),\
                        hostname=lsl_inlet.info().hostname(), channel_format='float64')
                self.lslobj[lsl_inlet.info().name()] = lsl


    def loadQuery(self):

        # Refreshes query every time query button is clicked
        self.clearLayout(self.streamQueryLayout)
        self.getAvailableStreams()


        if self.isAvailable:

            self.streamButtonGroup = QButtonGroup()

            for index, stream in enumerate(self.lslobj.keys()):
                info = self.lslobj[stream]

                streamInfo = "View %s?\n\t\t- Channel_Count: %d\n\t\t- Nominal_srate: %d\n\t\t- Channel_format: %s\n\t\t- UID: %s \n\t\t- Hostname: %s\n" % (stream, info.get_channel_count(), info.get_nominal_srate(), info.get_channel_format(), info.get_uid(), info.get_hostname())

                streamBtn = QRadioButton(streamInfo)
                streamBtn.setObjectName(stream)
                self.streamButtonGroup.addButton(streamBtn, index)
                self.streamQueryLayout.addWidget(streamBtn)

                streamBtn.clicked.connect(self.stream_clicked)

        else:
            item = QLabel(" No available streams that meet the given criteria!\n Please make sure that streams are running.")
            self.streamQueryLayout.addWidget(item)


    def clearLayout(self, layout):
        #for i in reversed(range(layout.count())): 
        #    layout.itemAt(i).widget().setParent(None)
        for cnt in reversed(range(layout.count())):
        # takeAt does both the jobs of itemAt and removeWidget
        # namely it removes an item and returns it
            widget = layout.takeAt(cnt).widget()
            widget.setVisible(False)
            widget.setParent(None)
            layout.removeWidget(widget)

            #if widget is not None: 
                # widget will be None if the item is a layout
            #    widget.deleteLater()

    def stream_clicked(self):
        self.currentStreamName = self.streamButtonGroup.checkedButton().objectName()
        self.loadChannels()


    def loadChannels(self):
        # Gets the name of the chosen stream needed under observation
        print("Load channels for {}".format(self.currentStreamName))

        self.clearLayout(self.channelLayout)
        self.showChannels.clear()


        # Resets signal viewer object for the new stream to be viewed
        #self.graph = None
        self.channelButtonGroup = QButtonGroup()
        self.channelButtonGroup.setExclusive(False)

        viewAllBtn = QCheckBox("View All Channels")

        viewAllBtn.setObjectName("View All")
        self.channelButtonGroup.addButton(viewAllBtn, 0)
        self.channelLayout.addWidget(viewAllBtn)

        viewAllBtn.clicked.connect(self.selectAllChannels)


        # Loads the available channels for the current stream under observation
        for index, channel in enumerate(self.lslobj[self.currentStreamName].get_channels()):
            channelBtn = QCheckBox("%s" % channel)
            channelID = index+1

            #channelBtn.setObjectName(channel)
            self.channelButtonGroup.addButton(channelBtn, channelID)
            self.channelLayout.addWidget(channelBtn)

        #self.channelButtonGroup.buttonClicked['QAbstractButton *'].connect(self.selectChannel)
        self.channelButtonGroup.buttonClicked['int'].connect(self.selectChannel)


    def clearChannels(self):
        pass

    def selectChannel(self, button_or_id):
        channelBtn = self.channelButtonGroup.checkedButton()
        #if channelBtn:
            #print(channelBtn.text())

        if isinstance(button_or_id, QAbstractButton):
            print('"{}" was clicked'.format(button_or_id.text()))

        elif isinstance(button_or_id, int) and button_or_id != 0:
            buttonID = button_or_id-1

            if buttonID in self.showChannels:
                self.showChannels.remove(buttonID)
            else:
                self.showChannels.append(buttonID)


    def selectAllChannels(self):
        viewAllBtn = self.channelButtonGroup.button(0)
        buttons = self.channelButtonGroup.buttons()[1:]

        if viewAllBtn.isChecked():
            for button in buttons:
                if not button.isChecked():
                    button.toggle()

            self.showChannels = [index for index, value in enumerate(buttons)]
        else:
            for button in buttons:
                if button.isChecked():
                    button.toggle()

            self.showChannels.clear()
            self.showChannels = []


    def pauseStream(self):
        self.graph.stop()


    def resumeStream(self):
        self.graph.start()

    
    def loadPauseResume(self):
        self.pauseBtn = QPushButton("Pause Stream")
        self.resumeBtn = QPushButton("Resume Stream")

        self.pauseView.addWidget(self.pauseBtn)
        self.resumeView.addWidget(self.resumeBtn)

        self.pauseBtn.clicked.connect(self.pauseStream)
        self.resumeBtn.clicked.connect(self.resumeStream)


    def loadFilters(self):

        self.filterScroll = QScrollArea()
        self.filtersBox = QGroupBox("Available Filters")
        self.filterScroll.setWidget(self.filtersBox)
        self.filterLayout2 = QVBoxLayout()
        self.filtersBox.setLayout(self.filterLayout2)
        self.filterLayout1.addWidget(self.filtersBox)

        self.filterButtonGroup = QButtonGroup()
        self.filterButtonGroup.setExclusive(False)

        notchBtn = QCheckBox("Notch")
        notchBtn.setObjectName("notch")
        self.filterButtonGroup.addButton(notchBtn, 0)
        self.filterLayout2.addWidget(notchBtn)

        butterBtn = QCheckBox("Butter")
        butterBtn.setObjectName("butter")
        self.filterButtonGroup.addButton(butterBtn, 1)
        self.filterLayout2.addWidget(butterBtn)

        self.applyFilterBtn = QPushButton("Apply Filter(s)")
        self.applyFilterLayout.addWidget(self.applyFilterBtn)
        self.applyFilterBtn.clicked.connect(self.applyFilters)

        self.filterButtonGroup.buttonClicked['QAbstractButton *'].connect(self.selectFilters)

    
    def selectFilters(self, button_or_id):
        if isinstance(button_or_id, QAbstractButton):
            if button_or_id.isChecked():
                self.filters[button_or_id.text()] = True
            else:
                self.filters[button_or_id.text()] = False


    def applyFilters(self):
        if any(self.filters):

            for Filter in self.filters.keys():
                if self.filters[Filter] == True:
                    print(Filter + " Applied")
                    self.graph.addFilter(Filter)
                else: 
                    self.graph.removeFilter(Filter)

            


    def showTSStream(self):
        if not self.lslobj:
            self.displayError("Please have ONE stream available to view.")

        elif len(self.showChannels) == 0:
            self.displayError("Please select only ONE channel to view.")

        else:
            if not self.TimeFrequencyLayout.isEmpty():
                    self.clearLayout(self.TimeFrequencyLayout)
                    self.graph.close_window()
                    self.graph = None

            if self.pauseView.isEmpty() and self.resumeView.isEmpty():
                    self.loadPauseResume()

            if self.filterLayout1.isEmpty():
                self.loadFilters()
            
            lsl_inlet = self.lslobj[self.currentStreamName]
            fs = lsl_inlet.get_nominal_srate()
            channels = lsl_inlet.get_channels()
            view_channels = [channel for channel in self.showChannels]#

            if not self.TimeSeriesLayout.isEmpty():
                self.graph.close()
                self.TimeSeriesViewer.removeWidget(self.graph)

            self.graph = TimeSeriesSignal(fs, channels, view_channels, lsl_inlet=lsl_inlet)
            self.TimeSeriesViewer.addWidget(self.graph)
            self.streamDataLayout.addWidget(self.graph.get_label())
            


    def showTFStream(self):
        if not self.lslobj:
            self.displayError("Please have ONE stream available to view.")

        elif len(self.showChannels) > 1 or len(self.showChannels) == 0:
            self.displayError("Please select only ONE channel to view.")
            
        else:

            if not self.TimeSeriesLayout.isEmpty():
                    self.graph.close_window()
                    self.graph = None
                    self.clearLayout(self.TimeSeriesLayout)

            if not self.filterLayout1.isEmpty():
                    self.clearLayout(self.filterLayout1)
                    self.clearLayout(self.filterLayout2)
                    self.clearLayout(self.applyFilterLayout)

            if self.pauseView.isEmpty() and self.resumeView.isEmpty():
                    self.loadPauseResume()

            if self.TimeFrequencyLayout.isEmpty():
                lsl_inlet = self.lslobj[self.currentStreamName]
            
                view_channel = self.showChannels[0]
                self.graph = SpectrumAnalyzer(lsl_inlet, view_channel)
                self.TimeFrequencyViewer.addWidget(self.graph)
            else:
                view_channel = self.showChannels[0]
                self.graph.resetChannel(view_channel)
            

    def displayError(self, error_message):
        errorBox = ErrorBox(message = error_message)
        errorBox.exec_()
   

    # Builds the GUI for the LSL app
    def initUI(self):

        self.queryBtn = self.findChild(QPushButton, 'queryButton')
        self.visualBtn = self.findChild(QPushButton, 'visualizeButton')
        self.timeFreqBtn = self.findChild(QPushButton, 'visualizeTimeFreqButton')
        self.queryStreams = self.findChild(QComboBox, 'availableStreams')
        self.streamName = self.findChild(QLineEdit, 'StreamName')

        self.TimeSeriesLayout = self.findChild(QGridLayout, 'TimeSeriesViewer')
        self.TimeFrequencyLayout = self.findChild(QGridLayout, 'TimeFrequencyViewer')
        self.pauseBtn = self.findChild(QGridLayout, 'pauseStream')
        self.resumeBtn = self.findChild(QGridLayout, 'resumeStream')
        self.filterLayout = self.findChild(QGridLayout, 'filtersBox')
        self.applyFilterLayout = self.findChild(QGridLayout, 'applyFilter')

        self.streamDataLayout = self.findChild(QVBoxLayout, 'streamData')
        self.streamMetaData = self.findChild(QLabel, 'streamLabel')
        self.streamMetaData.setAlignment(Qt.AlignCenter)
        self.streamDataLayout.addWidget(self.streamMetaData)

        self.pauseView = self.findChild(QGridLayout, 'pauseView')
        self.resumeView = self.findChild(QGridLayout, 'resumeView')

        logo = self.findChild(QLabel, 'UTKlogo')
        logo.setAlignment(Qt.AlignCenter)
        image = QPixmap("/Users/jdunkley98/Downloads/MABE-Research/lslbuffer/viz/UTKlogo.png")
        logo.setPixmap(image)

        label = self.findChild(QLabel, 'NBL')
        label.setAlignment(Qt.AlignCenter)

        self.channelScroll = self.findChild(QScrollArea, 'channelLayout')
        self.availableChannels = QGroupBox("Available Channels")
        self.channelScroll.setWidget(self.availableChannels)
        self.channelLayout = QVBoxLayout()
        self.availableChannels.setLayout(self.channelLayout)


        self.queryScroll = self.findChild(QScrollArea, 'queryStream')
        self.Query = QGroupBox("Available Streams")
        self.queryScroll.setWidget(self.Query)
        self.streamQueryLayout = QVBoxLayout()
        self.Query.setLayout(self.streamQueryLayout)


        self.filterLayout1 = self.findChild(QVBoxLayout, 'filterLayout')


        self.queryBtn.clicked.connect(self.loadQuery)
        self.visualBtn.clicked.connect(self.showTSStream)
        self.timeFreqBtn.clicked.connect(self.showTFStream)

        self.showMaximized()


    def exitHandler(self):
        for graph in self.graph_filters:
            graph.close_window()
            graph = None

        self.graph_filters.clear()
        self.graph_filters = None


    def mainWindowExitHandler(self):
        if self.graph is not None:
            self.graph.close_window()    

        for key in self.lslobj.keys():
            if self.lslobj[key]:
                del self.lslobj[key]
                self.lslobj[key] = None

        print("Exiting App.......")
        self.close()

if __name__ == "__main__":
    app=QApplication(sys.argv)  
    print("Starting up App.....")

    gui = LSLgui()

    app.aboutToQuit.connect(gui.mainWindowExitHandler)
    sys.exit(app.exec_())
