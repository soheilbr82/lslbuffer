#from queue import Queue
#from threading import Thread
#import time
from pylsl import StreamInlet, resolve_stream, StreamInfo, StreamOutlet
# Options for Ringbuffer
# Option 1:
# For having linked list
# import collections
# buffer_data = collections.deque()

# Option 2:
# For having numpy ringbuffer
import numpy as np
from numpy_ringbuffer import RingBuffer


class LSLRINGBUFFER:
    def __init__(self, lsl_type='EEG', fs=250, buffer_duration=4.0, num_channels=32):
  #      self.queue = queue
        self.lsl_type = lsl_type # Type of LSL that has to be parsed into the ring buffer
        self.fs = fs # Sampling rate of LSL
        self.buffer_duration = buffer_duration # Duration of Buffer
        self.num_channels = num_channels # Number of channels

    def run(self,queue):

        buffer_length = int(self.fs * self.buffer_duration)

        # Instantiate numpy_ringbuffer object with the required buffer size and number of channels
        buffer_data = RingBuffer(capacity=buffer_length, dtype=(float, self.num_channels))

        # first resolve an EEG stream on the lab network
        print("looking for an EEG stream...")
        streams = resolve_stream('type', self.lsl_type)
        # create a new inlet to read from the stream
        inlet = StreamInlet(streams[0])
        # Send data to the buffer
        while True:
            # get a new data chunk (you can also omit the timestamp part if you're not interested)
            sample, timestamp = inlet.pull_chunk()
            # If new chunk is received, then put in the buffer
            if timestamp:
                buffer_data.extend(np.array(sample))
            # Put the data in the thread
            queue.put(buffer_data)


