#PyQt5 modules
from PyQt5 import uic
from PyQt5.QtWidgets import*
from PyQt5.QtCore import*
from PyQt5.QtGui import*
import pyqtgraph as pg

#Self created modules
from application.Widgets.Logo import UTKLogo
from application.Widgets.Error import ErrorBox
from application.Widgets.FrequencyViewer_copy import SpectrumAnalyzer
from application.Widgets.TimeSeriesViewer import TimeSeriesSignal
from application.Widgets.QueryData import StreamData
from application.Buffers.lslringbuffer_multithreaded import LSLRINGBUFFER

#Python library modules
import pylsl
import sys

class LSLgui(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(LSLgui, self).__init__(*args, **kwargs)

        uic.loadUi("application/Visuals/LSL_visualization.ui", self) # Load the .ui file
        self.setWindowTitle('LSL Real-Time Analysis')   
        self.setMaximumSize(1150,1000) 

        self.avail_streams = dict()  # holds information about all of the availableStreams for the query
        self.availableFilters = {"Notch": False, "Butter": False}  # holds UI information for the various filters, i.e. notch and butter
        self.bands = {"Low" : None, "High": None} # Holds UI widgets for lowPass and highPass bands used for butter filter
        self.lslobj = dict() # Contains the lsl inlets for each stream object

        self.channels = []  # holds the QCheckList object for the channels for the current available stream
        self.showChannels = []  # holds the channels selected for visualization

        self.streamButtonGroup = None # Contains information about each stream button
        self.channelButtonGroup = None # Contains informations about each channel button for the current stream
        self.currentStreamName = None  # holds the current stream name of the stream wanting to be observed
        self.streamView = None
        self.graph = None # Contains the widget that displays either Time-Series data or Time-Frequency data

        self.initUI() 


    def getAvailableStreams(self):
        self.isAvailable = False # Resets availability of streams -> Always false unless stream is found
        self.lslobj.clear() # Clears container of lsl inlets for new batch of inlets

        streams = pylsl.resolve_streams(wait_time=1.0) # Contains information about all available lsl inlets

        # If streams list is empty, no streams are available
        # Clear the channelLayout of all previously listed channels, since no streams are available
        if len(streams) == 0:
            print("No streams available.")
            self.clearLayout(self.channelLayout)
            self.channelLayout.addWidget(QLabel("No available channels to view at this time."))

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
        self.Query.clear()
        self.clearLayout(self.channelLayout)
        self.channelLayout.addWidget(QLabel("No available channels to view at this time."))

        if self.streamButtonGroup is not None:
            self.clearButtonGroup(self.streamButtonGroup)
            self.streamButtonGroup = None

        self.getAvailableStreams()


        if self.isAvailable:

            self.streamButtonGroup = QButtonGroup()

            for index, stream in enumerate(self.lslobj.keys()):
                info = self.lslobj[stream]

                metaData = StreamData(["Name: %s - Type: %s" % (stream, info.get_stream_type())])
                self.Query.addTopLevelItem(metaData)

                metaData.addChildItem(QTreeWidgetItem(["Channel_Count: %d" % info.get_channel_count()]))
                metaData.addChildItem(QTreeWidgetItem(["Nominal_srate: %d" % info.get_nominal_srate()]))
                metaData.addChildItem(QTreeWidgetItem(["Channel_format: %s" % info.get_channel_format()]))
                metaData.addChildItem(QTreeWidgetItem(["uid: %s" % info.get_uid()]))
                metaData.addChildItem(QTreeWidgetItem(["Hostname: %s" % info.get_hostname()]))

                streamBtn = QRadioButton("View %s?" % stream)
                streamBtn.setObjectName(stream)
                streamBtn.clicked.connect(self.stream_clicked)

                # Keeps tracks of the selected stream
                self.streamButtonGroup.addButton(streamBtn, index)
                self.Query.setItemWidget(metaData, 1, streamBtn)

        else:
            item = QTreeWidgetItem(["No available streams that meet the given criteria!\nPlease make sure that streams are running."])
            self.Query.addTopLevelItem(item)


    def clearButtonGroup(self, buttonGroup):
        for button in buttonGroup.buttons():
            button.setParent(None)
            buttonGroup.removeButton(button)


    def clearLayout(self, layout):
        for cnt in reversed(range(layout.count())):
        # takeAt does both the jobs of itemAt and removeWidget
        # namely it removes an item and returns it
            widget = layout.takeAt(cnt).widget()
            widget.setVisible(False)
            widget.setParent(None)
            layout.removeWidget(widget)


    #Keeps track of which streamt the user wants to view
    #Once a stream is chosen, the corresponding channels are loaded in 
    #Another view to show which channels are available to view in the graph
    def stream_clicked(self):
        self.currentStreamName = self.streamButtonGroup.checkedButton().objectName()
        
        self.clearLayout(self.channelLayout)

        if self.channelButtonGroup is not None:
            self.clearButtonGroup(self.channelButtonGroup)

        self.showChannels.clear()
        self.loadChannels()


    def loadChannels(self):
        # Gets the name of the chosen stream needed under observation
        print("Load channels for {}".format(self.currentStreamName))


        # Resets signal viewer object for the new stream to be viewed
        self.channelButtonGroup = QButtonGroup()
        self.channelButtonGroup.setExclusive(False)

        viewAllBtn = QCheckBox("View All Channels")
        viewAllBtn.setObjectName("View All")

        self.channelButtonGroup.addButton(viewAllBtn, 0)
        self.channelLayout.addWidget(viewAllBtn)

        viewAllBtn.clicked.connect(self.selectAllChannels)


        # Loads the available channels for the current stream under observation
        for index, c in enumerate(self.lslobj[self.currentStreamName].get_channels()):
            channelBtn = QCheckBox(c)
            channelBtn.setObjectName(c)
            channelID = index+1

            self.channelButtonGroup.addButton(channelBtn, channelID)
            self.channelLayout.addWidget(channelBtn)

        self.channelButtonGroup.buttonClicked['int'].connect(self.selectChannel)


    #Keeps track of each individual channel selected for viewing
    def selectChannel(self, button_or_id):
        channelBtn = self.channelButtonGroup.checkedButton()

        if isinstance(button_or_id, QAbstractButton):
            print('"{}" was clicked'.format(button_or_id.text()))

        elif isinstance(button_or_id, int) and button_or_id != 0:
            buttonID = button_or_id-1

            if buttonID in self.showChannels:
                self.showChannels.remove(buttonID)
            else:
                self.showChannels.append(buttonID)


    #If the "View All Channels" button is selected
    #This method either selects all channels to view
    #Or removes all channels from the viewing list
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


    #Pauses the streaming data
    def pauseStream(self):
        self.graph.stop()


    #Resumes the streaming data
    def resumeStream(self):
        self.graph.start()

    
    #Displays the pause and resume buttons for the Time-Series/Frequency data
    def loadPauseResume(self):
        self.pauseBtn = QPushButton("Pause Stream")
        self.resumeBtn = QPushButton("Resume Stream")

        self.pauseView.addWidget(self.pauseBtn)
        self.resumeView.addWidget(self.resumeBtn)

        self.pauseBtn.clicked.connect(self.pauseStream)
        self.resumeBtn.clicked.connect(self.resumeStream)


    #Displays the filter options to apply to the Time-Series data
    #Filter buttons are kept track of using a QButtonGroup container
    def loadFilters(self):

        self.Filters = QTreeWidget()
        self.Filters.setColumnCount(2)
        self.Filters.header().setSectionResizeMode(3)
        self.filterLayout1.addWidget(self.Filters)

        self.filterButtonGroup = QButtonGroup()
        self.filterButtonGroup.setExclusive(False)

        notch = QTreeWidgetItem(["Notch Filter"])
        self.Filters.addTopLevelItem(notch)

        butter = QTreeWidgetItem(["Butter Filter"])
        self.Filters.addTopLevelItem(butter)

        i1 = QTreeWidgetItem(["Low Pass"])
        i2 = QTreeWidgetItem(["High Pass"])
        butter.addChild(i1)
        butter.addChild(i2)

        self.bands["Low"] = QLineEdit()
        self.bands["Low"].setFixedHeight(30)
        self.bands["Low"].setFixedWidth(125)
        self.lowPass = None

        self.bands["High"] = QLineEdit()
        self.bands["High"].setFixedHeight(30)
        self.bands["High"].setFixedWidth(125)
        self.highPass = None

        self.bands["Low"].editingFinished.connect(self.applyLowPass)
        self.bands["High"].editingFinished.connect(self.applyHighPass)

        notchBtn = QCheckBox("Notch")
        notchBtn.setObjectName("notch")
        self.filterButtonGroup.addButton(notchBtn, 0)

        butterBtn = QCheckBox("Butter")
        butterBtn.setObjectName("butter")
        self.filterButtonGroup.addButton(butterBtn, 1)

        self.Filters.setItemWidget(notch, 1, notchBtn)
        self.Filters.setItemWidget(butter, 1, butterBtn)
        self.Filters.setItemWidget(i1, 1, self.bands["Low"])
        self.Filters.setItemWidget(i2, 1, self.bands["High"])

        self.applyFilterBtn = QPushButton("Apply Filter(s)")
        self.applyFilterLayout.addWidget(self.applyFilterBtn)
        self.applyFilterBtn.clicked.connect(self.applyFilters)

        self.filterButtonGroup.buttonClicked['QAbstractButton *'].connect(self.selectFilters)

    #Senses when the user changes the text in the low pass text box
    #And applies a low pass filter to the window with the Butter Filter applied
    def applyLowPass(self,):
        if self.availableFilters["Butter"] == True:
            if len(self.bands["Low"].text()) == 0:
                self.lowPass = 0.1
            else:
                if 0.1 <= float(self.bands["Low"].text()):
                    self.lowPass = float(self.bands["Low"].text())

            self.graph.changeFilter("Butter", (self.lowPass, self.highPass))

    #Senses when the user changes the text in the high pass text box
    #And applies a high pass filter to the window with the Butter Filter applied
    def applyHighPass(self,):
        if self.availableFilters["Butter"] == True:
            if len(self.bands["High"].text()) == 0:
                self.highPass = (self.lslobj[self.currentStreamName].get_nominal_srate() / 2) - .001
            else:
                if float(self.bands["High"].text()) < self.lslobj[self.currentStreamName].get_nominal_srate() / 2:
                    self.highPass = float(self.bands["High"].text())

            self.graph.changeFilter("Butter", (self.lowPass, self.highPass))

    
    #Keeps track of what filters are wanting to be applied by the user
    def selectFilters(self, button_or_id):
        if isinstance(button_or_id, QAbstractButton):
            if button_or_id.isChecked():
                self.availableFilters[button_or_id.text()] = True
            else:
                self.availableFilters[button_or_id.text()] = False


    #Checks to see if any filters are wanting to be applied by the user
    #If so, it creates a new window with the filter applied
    #Else, it destroys any existing windows with filters applied
    def applyFilters(self):
        if any(self.availableFilters):

            for f in self.availableFilters.keys():
                if self.availableFilters[f] == True:
                    self.graph.addFilter(f)
                else: 
                    self.graph.removeFilter(f)


    def showTSStream(self):

        #Check is stream have been queried and at least ONE stream is selected to vizualize
        if not self.lslobj:
            self.displayError("Please have ONE stream available to view.")

        #Check to see if at least ONE channel has been chosen to visualize from the current stream
        elif len(self.showChannels) == 0:
            self.displayError("Please select only ONE channel to view.")

        else:
            #Check is Time Frequency is in use
            #If it is, clear the layout to ensure clear visibility of the Time Series Graph
            if not self.FrequencyLayout.isEmpty():
                    self.clearLayout(self.FrequencyLayout)
                    self.graph.close_window()
                    self.graph = None

            #Check is pause/resume buttons have been displayed from a previous graph
            #If they are not displayed, create and display them
            if self.pauseView.isEmpty() and self.resumeView.isEmpty():
                    self.loadPauseResume()

            #Check to see if the filter options are available to view from a previous graph
            #If they are not displayed, create and display them
            if self.filterLayout1.isEmpty():
                self.loadFilters()
            
            #Obtain the current stream inlet to pass into the Signal Viewer
            lsl_inlet = self.lslobj[self.currentStreamName]
            fs = lsl_inlet.get_nominal_srate()
            channels = lsl_inlet.get_channels()
            view_channels = [channel for channel in self.showChannels]

            #If another Time Series graph is being visualized
            #Remove the current graph and replace with a new one with a different set of arguments to use
            if not self.TimeSeriesLayout.isEmpty():
                self.graph.close()
                self.TimeSeriesViewer.removeWidget(self.graph)


            self.graph = TimeSeriesSignal(fs, channels, view_channels, lsl_inlet=lsl_inlet)
            self.TimeSeriesViewer.addWidget(self.graph)

            #Ensures multiple copies of the meta data are not created with each click of "Visualize Time Series"
            self.clearLayout(self.streamDataLayout)
            self.streamDataLayout.addWidget(self.graph.getMetaData())



    def showTFStream(self):
        #Check is stream have been queried and at least ONE stream is selected to vizualize
        if not self.lslobj:
            self.displayError("Please have ONE stream available to view.")

        #Check to see that only ONE channel has been chosen to visualize from the current stream
        elif len(self.showChannels) > 1 or len(self.showChannels) == 0:
            self.displayError("Please select only ONE channel to view.")
            
        else:

            #Check is Time Series is in use
            #If it is, clear the layout to ensure clear visibility of the Time Frequency Graph
            if not self.TimeSeriesLayout.isEmpty():
                self.graph.close_window()
                self.graph = None
                self.clearLayout(self.TimeSeriesLayout)

            #Check to see if filter options are available
            #If they are, remove them since the Time Frequency graph does not require the use of filters
            if not self.filterLayout1.isEmpty():
                self.clearLayout(self.filterLayout1)
                self.clearButtonGroup(self.filterButtonGroup)
                self.clearLayout(self.applyFilterLayout)
            
            #Check to see if the meta data from the Time Series graph is still visible
            #If it is, remove the label and clear the layout
            if not self.streamDataLayout.isEmpty():
                self.clearLayout(self.streamDataLayout)

            #Check is pause/resume buttons have been displayed from a previous graph
            #If they are not displayed, create and display them
            if self.pauseView.isEmpty() and self.resumeView.isEmpty():
                    self.loadPauseResume()

            #If this is the first time the Time Frequency graph is being used
            #Get the current stream inlet and the selected channel to view
            #Pass these in as arguments to create a SpectrumAnalyzer object
            if self.FrequencyLayout.isEmpty():
                lsl_inlet = self.lslobj[self.currentStreamName]
            
                view_channel = self.showChannels[0]
                self.graph = SpectrumAnalyzer(lsl_inlet, view_channel)
                self.FrequencyViewer.addWidget(self.graph)

            #Resets the channel currently in the graph with the newly selected channel
            else:
                view_channel = self.showChannels[0]
                self.graph.resetChannel(view_channel)
            

    #Displays an error message specified by the programmer
    def displayError(self, error_message):
        errorBox = ErrorBox(message = error_message)
        errorBox.exec_()
   

    # Builds the GUI for the LSL app
    def initUI(self):

        self.queryBtn = self.findChild(QPushButton, 'queryButton')
        self.visualBtn = self.findChild(QPushButton, 'visualizeButton')
        self.freqBtn = self.findChild(QPushButton, 'visualizeFreqButton')

        self.TimeSeriesLayout = self.findChild(QGridLayout, 'TimeSeriesViewer')
        self.FrequencyLayout = self.findChild(QGridLayout, 'FrequencyViewer')
        self.pauseBtn = self.findChild(QGridLayout, 'pauseStream')
        self.resumeBtn = self.findChild(QGridLayout, 'resumeStream')
        self.filterLayout = self.findChild(QGridLayout, 'filtersBox')
        self.applyFilterLayout = self.findChild(QGridLayout, 'applyFilter')

        self.streamDataLayout = self.findChild(QVBoxLayout, 'streamData')

        self.pauseView = self.findChild(QGridLayout, 'pauseView')
        self.resumeView = self.findChild(QGridLayout, 'resumeView')

        logo = self.findChild(QLabel, 'UTKlogo')
        logo.setAlignment(Qt.AlignCenter)
        image = QPixmap("application/Visuals/UTKlogo.png")
        logo.setPixmap(image)

        label = self.findChild(QLabel, 'NBL')
        label.setAlignment(Qt.AlignCenter)

        self.channelScroll = self.findChild(QScrollArea, 'channelLayout')
        self.channelLayout = QVBoxLayout()
        self.channelScroll.setLayout(self.channelLayout)

        self.channelScroll = self.findChild(QScrollArea, 'channelLayout')
        self.availableChannels = QWidget()
        self.availableChannels.setStyleSheet('background-color: white')        
        self.channelScroll.setWidget(self.availableChannels)
        self.channelScroll.setWidgetResizable(True)
        self.channelLayout = QVBoxLayout(self.availableChannels)
        self.availableChannels.setLayout(self.channelLayout)
        self.channelLayout.addWidget(QLabel("No available channels to view at this time."))

        self.queryScroll = self.findChild(QScrollArea, 'queryStream')

        self.Query = QTreeWidget()
        self.Query.setColumnCount(2)
        self.Query.header().setSectionResizeMode(3)
        self.queryScroll.setWidget(self.Query)


        self.filterLayout1 = self.findChild(QVBoxLayout, 'filterLayout')

        self.queryBtn.clicked.connect(self.loadQuery)
        self.visualBtn.clicked.connect(self.showTSStream)
        self.freqBtn.clicked.connect(self.showTFStream)

        self.showMaximized()

    #Ensures a clean exit of the main application window
    #Closes all graphs and disconnects and lsl inlets
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
