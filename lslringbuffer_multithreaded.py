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
    def __init__(self, lsl_type='EEG', name=None, inlet=None, fs=250, buffer_duration=4.0, num_channels=32, filter=filter, uid=None, hostname=None, channel_format='float32'):
        #      self.queue = queue
        self.lsl_type = lsl_type  # Type of LSL that has to be parsed into the ring buffer
        self.stream_name=name
        self.inlet = inlet
        self.fs = fs  # Sampling rate of LSL
        self.buffer_duration = buffer_duration  # Duration of Buffer
        self.num_channels = num_channels  # Number of channels
        self.channels = ['Ch %i' % i for i in range(self.num_channels)]
        self.uid = uid 
        self.hostname = hostname
        self.channel_format = channel_format
        self.filter = filter
        self.chunk=None

    def run(self, stop, buffer_queue, chunk_queue=None):

        buffer_length = int(self.fs * self.buffer_duration)

        # Instantiate numpy_ringbuffer object with the required buffer size and number of channels
        buffer_data = RingBuffer(capacity=buffer_length, dtype=(float, self.num_channels))

        # create a new inlet to read from the stream
        #inlet = lsl 
        # Send data to the buffer
        while True:
            
            #For threading
            #If the state flag has changed, stop reading in data for the thread
            if stop():
                print("Thread stopped")
                break

            # get a new data chunk (you can also omit the timestamp part if you're not interested)
            #self.chunk = self.pull_next_chunk()
            sample, timestamp = self.get_next_chunk()#get_next_chunk()
            
            
            # If new chunk is received, then put in the buffer
            if timestamp:
                #print(sample.shape)
                buffer_data.extend(np.array(sample))
                # Put the data in the thread
                buffer_queue.put(buffer_data)
                if chunk_queue:
                    chunk_queue.put(np.array(sample))

    def get_next_chunk(self):
        # get next chunk
        chunk, timestamp = self.inlet.pull_chunk()
        # convert to numpy array
        chunk = np.array(chunk, dtype=self.get_channel_format())
        # return first n_channels channels or None if empty chunk
        return (chunk, timestamp) if chunk.shape[0] > 0 else (None, None)

    def get_stream_type(self):
        return self.lsl_type

    def get_nominal_srate(self):   
        return self.fs
    
    def get_channel_count(self):
        return self.num_channels
    
    def get_channels(self):
        return self.channels

    def get_uid(self):
        return self.uid 

    def get_hostname(self):
        return self.hostname

    def get_channel_format(self):
        return self.channel_format


if __name__ == "__main__":
    lsl = LSLRINGBUFFER(lsl_type='EEG', fs=250, buffer_duration=4.0, num_channels=32, filter=notch)
    lsl.run()
