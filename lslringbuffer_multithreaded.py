from queue import Queue
from threading import Thread
import time
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
    def __init__(self, lsl_type='EEG', fs=250, buffer_duration=4.0, num_channels=32, filter=filter):
        #      self.queue = queue
        self.lsl_type = lsl_type  # Type of LSL that has to be parsed into the ring buffer
        self.fs = fs  # Sampling rate of LSL
        self.buffer_duration = buffer_duration  # Duration of Buffer
        self.num_channels = num_channels  # Number of channels
        self.filter = filter

    def run(self, stop, queue, lsl):

        buffer_length = int(self.fs * self.buffer_duration)

        # Instantiate numpy_ringbuffer object with the required buffer size and number of channels
        buffer_data = RingBuffer(capacity=buffer_length, dtype=(float, self.num_channels))

        # create a new inlet to read from the stream
        inlet = lsl 
        # Send data to the buffer
        while True:
            
            #For threading
            #If the state flag has changed, stop reading in data for the thread
            if stop():
                print("Thread stopped")
                break

            # get a new data chunk (you can also omit the timestamp part if you're not interested)
            sample, timestamp = inlet.get_next_chunk()#pull_chunk()
            
            # If new chunk is received, then put in the buffer
            if timestamp:
                buffer_data.extend(np.array(sample))
                # Put the data in the thread
                queue.put(buffer_data)


class BaseFilter:
    def apply(self, chunk: np.ndarray):
        '''
        :param chunk:
        :return:
        '''
        raise NotImplementedError


class NotchFilter(BaseFilter):
    def __init__(self, f0, fs, n_channels, mu=0.05):
        self.n_channels = n_channels
        w0 = 2 * np.pi * f0 / fs
        self.a = np.array([1., 2 * (mu - 1) * np.cos(w0), (1 - 2 * mu)])
        self.b = np.array([1., -2 * np.cos(w0), 1.]) * (1 - mu)
        self.zi = np.zeros((max(len(self.b), len(self.a)) - 1, n_channels))

    # def apply(self, chunk: np.ndarray):
    #     y, self.zi = lfilter(self.b, self.a, chunk, axis=0, zi=self.zi)
    #     return y

    def reset(self):
        self.zi = np.zeros((max(len(self.b), len(self.a)) - 1, self.n_channels))


if __name__ == "__main__":
    notch = NotchFilter(50, 250, 32)
    lsl = LSLRINGBUFFER(lsl_type='EEG', fs=250, buffer_duration=4.0, num_channels=32, filter=notch)
    lsl.run()
