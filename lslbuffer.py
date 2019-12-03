from __future__ import division

import time
import logging

import numpy as np
import pylsl
from pylsl import StreamInlet, resolve_byprop, resolve_bypred
from pylsl.pylsl import lib, StreamInfo, FOREVER, c_int, c_double, byref, handle_error
import time
import socket
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)
logger.info('Logger started.')


class LSLBUFFER():
    """lab streaming layer (lsl) with varied buffer size and time-corrected samples.
    By running this code you can connect to a running EEG device that is
    publishing its data to lsl stream. With this class you can initiate a buffer size of
    your choice.
    https://code.google.com/p/labstreaminglayer/
    Examples
    --------
        >>> lslobj = LSLBUFFER(stream_type='EEG', buffer_size=4.0)
        >>> lslobj.configure()
        >>> lslobj.start()
        >>> while True:
        ...     data, marker = lslobj.get_data()
        ...     # do something with data and/or break the loop
        >>> obj.stop()
    """

    def __init__(self, stream_type='EEG', buffer_size=4.0):

        self.stream_type = stream_type  # stream type
        self.buffer_size = buffer_size  # Buffer size (second)
        self.eeg_stream_name = None

    def configure(self, **kwargs):
        """Configure the lsl stream.
        This method finds running lsl streams and picks the first `EEG`
        and `Markers` streams.
        """

        # open EEG lsl stream
        logger.debug('Opening EEG stream...')
        eeg_streams = pylsl.resolve_byprop('type', 'EEG', timeout=2)
        try:
            if len(eeg_streams) == 0:
                self.bool_eeg_streams = False
                # raise RuntimeError("Can't find EEG stream")
            if len(eeg_streams) > 1:
                self.bool_eeg_streams = True
                logger.warning('Number of EEG streams is > 0, picking the first one.')
        except RuntimeError as x:
            print("Can't find EEG stream")

        self.eeg_stream_name = pylsl.StreamInfo.name(eeg_streams[0])
        print(self.eeg_stream_name + " is found!")
        self.lsl_inlet = pylsl.StreamInlet(eeg_streams[0])
        # lsl time sample correction
        self.lsl_inlet.time_correction()

        # open marker lsl stream
        logger.debug('Opening Marker stream...')
        # TODO: should add a timeout here in case there is no marker
        # stream
        marker_streams = pylsl.resolve_byprop('type', 'Markers', timeout=2)
        if marker_streams:
            self.bool_marker_streams = True
            if len(marker_streams) > 1:
                logger.warning('Number of Marker streams is > 0, picking the first one.')

            marker_stream_name = pylsl.StreamInfo.name(marker_streams[0])
            print(marker_stream_name + " is found!")
            self.lsl_marker_inlet = pylsl.StreamInlet(marker_streams[0])
            # lsl time sample correction
            self.lsl_marker_inlet.time_correction()
        else:
            self.bool_marker_streams = False
            print("Can't find Markers stream")

        # Parse channel name and sampling frequency
        info = self.lsl_inlet.info()
        #       self.fs = pylsl.StreamInfo.nominal_srate(eeg_streams[0])

        self.n_channels = info.channel_count()
        self.channels = ['Ch %i' % i for i in range(self.n_channels)]
        self.fs = info.nominal_srate()
        logger.debug('Initializing time correction...')

        # lsl buffer defined
        self.max_samples = int(self.fs * self.buffer_size)
        logger.debug('Configuration done.')

    def start(self):
        """Open the lsl inlets.
        """
        logger.debug('Opening lsl streams.')
        self.lsl_inlet.open_stream()

        if self.bool_marker_streams:
            self.lsl_marker_inlet.open_stream()

    def stop(self):
        """Close the lsl inlets.
        """
        logger.debug('Closing lsl streams.')
        self.lsl_inlet.close_stream()

        if self.bool_marker_streams:
            self.lsl_marker_inlet.close_stream()

    def get_data(self):
        """Receive a chunk of data an markers.
        Returns
        -------
        chunk, markers: Markers is time in ms since relative to the
        first sample of that block.
        """

        tc_s = self.lsl_inlet.time_correction()
        if self.bool_marker_streams:
            tc_m = self.lsl_marker_inlet.time_correction()
            markers, m_timestamps = self.lsl_marker_inlet.pull_chunk(timeout=0.0, max_samples=self.max_samples)
            # flatten the output of the lsl markers, which has the form
            # [[m1], [m2]], and convert to string
            markers = [str(i) for sublist in markers for i in sublist]

            # block until we actually have data
            samples, timestamps = self.lsl_inlet.pull_chunk(timeout=pylsl.FOREVER, max_samples=self.max_samples)
            samples = np.array(samples).reshape(-1, self.n_channels)

            t0 = timestamps[0] + tc_s
            m_timestamps = [(i + tc_m - t0) * 1000 for i in m_timestamps]

            return samples, zip(m_timestamps, markers)

        else:
            # block until we actually have data
            samples, timestamps = self.lsl_inlet.pull_chunk(timeout=pylsl.FOREVER, max_samples=self.max_samples)
            samples = np.array(samples).reshape(-1, self.n_channels)

            return samples

    def get_channels(self):
        """Get channel names.
        """
        return self.channels

    def get_sampling_frequency(self):
        """Get the nominal sampling frequency of the EEG lsl stream.
        """
        return self.fs


global LSL_STREAM_NAMES
# global LSL_RESOLVE_TIMEOUT
#
LSL_STREAM_NAMES = ['AudioCaptureWin', 'NVX136_Data', 'EEG']
# LSL_RESOLVE_TIMEOUT = 10
#
#
# class FixedStreamInfo(StreamInfo):
#     def as_xml(self):
#         return lib.lsl_get_xml(self.obj).decode('utf-8', 'ignore')  # add ignore
#
#
# class FixedStreamInlet(StreamInlet):
#     def info(self, timeout=FOREVER):
#         errcode = c_int()
#         result = lib.lsl_get_fullinfo(self.obj, c_double(timeout),
#                                       byref(errcode))
#         handle_error(errcode)
#         return FixedStreamInfo(handle=result)  # StreamInfo(handle=result)


class LSLInlet:
    def __init__(self, stream, name=LSL_STREAM_NAMES[2], only_this_host=False):
        """if not only_this_host:
            streams = resolve_byprop('name', name, timeout=LSL_RESOLVE_TIMEOUT)
        else:
            streams = resolve_bypred("name='{}' and hostname='{}'".format(name, socket.gethostname()))
        """
        self.stream_type = name
        self.inlet = None
        self.dtype = 'float64'
        self.stream_name = pylsl.StreamInfo.name(stream)
        # self.fs = pylsl.StreamInfo.nominal_srate(stream)

        print("Trying to connect to {} LSL stream.....".format(self.stream_name))

        try:
            # if len(streams) > 0:
            self.inlet = pylsl.StreamInlet(stream, max_buflen=4)

            # def start(self):
            """Open the lsl inlets.
            """
            logger.debug('Opening lsl streams.')
            self.inlet.open_stream()
            # self.dtype = fmt2string[self.inlet.info().channel_format()]
            print('Connected to {} LSL stream successfully'.format(name))
            self.n_channels = self.inlet.info().channel_count()
            self.channels = ['Ch %i' % i for i in range(self.n_channels)]

            # else:
            #    raise ConnectionError('Cannot connect to "{}" LSL stream'.format(name))
        except ConnectionError as e:
            print('Cannot connect to "{}" LSL stream'.format(name))

    def get_next_chunk(self):
        # get next chunk
        chunk, timestamp = self.inlet.pull_chunk()
        # convert to numpy array
        chunk = np.array(chunk, dtype=self.dtype)
        # return first n_channels channels or None if empty chunk
        return (chunk, timestamp) if chunk.shape[0] > 0 else (None, None)

    def update_action(self):
        pass

    def save_info(self, file):
        with open(file, 'w') as f:
            f.write(self.info_as_xml())

    def info_as_xml(self):
        xml = self.inlet.info().as_xml()
        return xml

    def get_frequency(self):
        return self.inlet.info().nominal_srate()

    def get_channels(self):
        """Get channel names.
        """
        return self.channels

    def get_n_channels(self):
        return self.inlet.info().channel_count()

    def get_channels_labels(self):
        for t in range(3):
            time.sleep(0.5 * (t + 1))
            try:
                # print('wow') TODO too many repetitions
                rt = ET.fromstring(self.info_as_xml())
                channels_tree = rt.find('desc').findall("channel") or rt.find('desc').find("channels").findall(
                    "channel")
                labels = [(ch.find('label') if ch.find('label') is not None else ch.find('name')).text
                          for ch in channels_tree]
                return labels
            except OSError:
                print('OSError during reading channels names', t + 1)
        return ['channel' + str(n + 1) for n in range(self.get_n_channels())]

    def disconnect(self):
        del self.inlet
        self.inlet = None
