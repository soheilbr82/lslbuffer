import numpy as np
import pyqtgraph as pg
import os
import pylsl
from scipy import signal, stats
from PyQt5.QtWidgets import*


# import sys
# from pynfb.signal_processing.filters import NotchFilter, IdentityFilter, FilterSequence

paired_colors = ['#dbae57', '#57db6c', '#dbd657', '#57db94', '#b9db57', '#57dbbb', '#91db57', '#57d3db', '#69db57',
                 '#57acdb']
images_path = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + '/../static/imag') + '/'


class SignalViewer(QWidget):
    def __init__(self, fs, names, view_channels, seconds_to_plot, overlap, signals_to_plot=None,
                 **kwargs):
        super(SignalViewer, self).__init__(**kwargs)
        # gui settings

        self.vb = CustomViewBox()
        self.lay = QVBoxLayout()
        self.specWid = pg.PlotWidget(name="Time-Series Graph")
        #self.setTitle("Time-Series Graph")
        self.specWid.plotItem.setMouseEnabled(x=False)
        self.specWid.plotItem.showGrid(y=True)
        #self.getPlotItem().enableAutoRange(axis='y')
        #self.getPlotItem().setMenuEnabled(enableMenu=False)
        #self.getPlotItem().setMouseEnabled(x=False)
        #self.getPlotItem().autoBtn.disable()
        #self.getPlotItem().autoBtn.setScale(0)
        self.specWid.plotItem.setRange(xRange=(0, seconds_to_plot))
        self.specWid.setBackgroundBrush(pg.mkBrush('#252120'))
        self.lay.addWidget(self.specWid)
        self.createTimer()
        self.show()

        # init buffers
        self.names = []
        self.indices = view_channels

        for i, n in enumerate(names):
            if i in view_channels:
                self.names.append(n)

        self.n_signals = len(self.names)
        self.n_signals_to_plot = self.n_signals  # min(self.n_signals, signals_to_plot or self.n_signals)
        self.n_samples = int(fs * seconds_to_plot)  # samples to show
        self.x_stamps = np.arange(self.n_samples)
        # Received samples counter
        self.previous_pos = 0
        self.pos = 0
        self.x_mesh = np.linspace(0, seconds_to_plot, self.n_samples)
        self.y_raw_buffer = np.zeros(shape=(self.n_samples, self.n_signals)) * np.nan

        # set names
        if overlap:
            self.specWid.getPlotItem().addLegend(offset=(-30, 30))

        # init signal curves
        self.curves = []
        for i in range(self.n_signals_to_plot):
            curve = pg.PlotDataItem(pen=paired_colors[i % len(paired_colors)], name=names[i])
            self.specWid.addItem(curve)
            if not overlap:
                curve.setPos(0, i + 1)
            self.curves.append(curve)

        # add vertical running line
        self.vertical_line = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen(color='B48375', width=1))
        self.specWid.addItem(self.vertical_line)


    def createTimer(self):
        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self.main_loop)
        self.main_timer.start(30)


    def update(self, chunk, setX=None, setPos=None):
        # estimate current pos
        chunk_len = len(chunk)
        current_pos = (self.previous_pos + chunk_len) % self.n_samples
        if setX and setPos and self.pos != 0:
            self.current_x = setX
            self.current_pos = setPos
            self.pos = 0
        else:
            self.current_x = self.x_mesh[current_pos]
            self.current_pos = (self.previous_pos + chunk_len) % self.n_samples

        # update buffer
        if self.previous_pos < self.current_pos:
            self.y_raw_buffer[self.previous_pos:self.current_pos] = chunk[:, np.array(self.indices)]
        else:
            self.y_raw_buffer[self.previous_pos:] = chunk[:self.n_samples - self.previous_pos, np.array(self.indices)]
            if self.current_pos > 0:
                self.y_raw_buffer[:self.current_pos] = chunk[self.n_samples - self.previous_pos:,
                                                       np.array(self.indices)]

        # pre-process y data and update it
        y_data = self.y_raw_buffer#self.prepare_y_data(chunk_len)
        before_mask = (self.x_stamps < self.current_pos)
        for i, curve in enumerate(self.curves):
            y = y_data[:, i] if i < y_data.shape[1] else self.x_mesh * np.nan
            curve.setData(self.x_mesh, y, connect=np.isfinite(y) | before_mask)
        self.vertical_line.setValue(self.current_x)

        # update pos
        self.previous_pos = self.current_pos

    #This function is overriden in the Child class RawSignalViewer
    def prepare_y_data(self, chunk_len):
        return self.y_raw_buffer

    def reset_buffer(self):
        self.y_raw_buffer *= np.nan
        
class RawSignalViewer(SignalViewer):
    """
    Plot raw data, each channel is on separate line
    """

    def __init__(self, fs, names, view_channels, seconds_to_plot=5, **kwargs):

        super(RawSignalViewer, self).__init__(fs, names, view_channels, seconds_to_plot=seconds_to_plot, overlap=False,
                                              signals_to_plot=5, **kwargs)
        # gui settings
        self.specWid.getPlotItem().setYRange(0, self.n_signals_to_plot + 1)
        self.specWid.getPlotItem().disableAutoRange()
        #self.getPlotItem().enableAutoRange(axis='y')

        self.names = []
        self.indices = view_channels

        for i, n in enumerate(names):
            if i in view_channels:
                self.names.append(n)

        self.mean = np.zeros(self.n_signals)
        self.iqr = np.ones(self.n_signals)
        self.stats_update_counter = 0
        self.indexes_to_plot = [slice(j, self.n_signals) for j in range(0, self.n_signals)]
        self.current_indexes_ind = 0
        self.c_slice = self.indexes_to_plot[self.current_indexes_ind]
        self.reset_labels()

    def next_channels_group(self, direction=1):
        self.y_raw_buffer *= np.nan
        self.current_indexes_ind = (self.current_indexes_ind + direction) % len(self.indexes_to_plot)
        self.c_slice = self.indexes_to_plot[self.current_indexes_ind]
        self.reset_labels()
        pass

    def reset_labels(self):
        ticks = [[(val, tick) for val, tick in zip(range(1, self.n_signals_to_plot + 1), self.names[self.c_slice])]]
        self.specWid.getPlotItem().getAxis('left').setTicks(ticks)

    #Overrides prepare_y_data from SignalViewer
    #This function scales the EEG signal to fit the size of the window
    #This function is called in the base class
    #def prepare_y_data(self, chunk_len):
    #  # update scaling stats
    #    self.stats_update_counter += chunk_len
    #    if self.stats_update_counter > self.n_samples // 3:
    #        self.mean = np.nanmean(self.y_raw_buffer, 0)
    #        self.iqr = stats.iqr(self.y_raw_buffer, 0, rng=(0, 100), nan_policy='omit')
    #        self.iqr[self.iqr <= 0] = 1
    #        self.stats_update_counter = 0
    #
    #    # return scaled signals
    #    return ((self.y_raw_buffer - self.mean) / self.iqr)[:, self.c_slice]


class DerivedSignalViewer(SignalViewer):
    """
    Plot overlapped signals
    """

    def __init__(self, fs, names, seconds_to_plot=5, **kwargs):
        super(DerivedSignalViewer, self).__init__(fs, names, seconds_to_plot, overlap=True, **kwargs)



# Override the pg.ViewBox class to add custom
# implementations to the wheelEvent
class CustomViewBox(pg.ViewBox):
    def __init__(self, *args, **kwds):
        pg.ViewBox.__init__(self, *args, **kwds)
        #self.setMouseMode(self.RectMode)

    def wheelEvent(self, ev, axis=None):
        # 1. Determine initial x-range
        initialRange = self.viewRange()

        # 2. Call the superclass method for zooming in
        pg.ViewBox.wheelEvent(self,ev,axis)

        # 3. Reset the x-axis to its original limits
        self.setXRange(initialRange[0][0],initialRange[0][1])