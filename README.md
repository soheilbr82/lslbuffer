
# Generate Dummy data in LSL


If you want to run the program without the OpenBCI headset, and just output dummy data, use the `--dummy` flag

```bash
python -m start_stream
```
When running the program:
* To stop streaming data, enter `/stop`
* To start streaming data again, enter `/start`
* To exit the program, enter `/exit`



# lslbuffer

The class provides a variable size buffer of EEG received stream through labstreaminglayer (lsl)

```python
import lslbuffer as lb
lslobj = lb.LSLBUFFER(stream_type='EEG', buffer_size=4.0)
lslobj.configure()
lslobj.start()
while True:
	data, marker = lslobj.get_data()
    # do something with data and/or break the loop
lslobj.stop()
```




# lslringbuffer

The class provides a variable size ringbuffer of EEG received stream through labstreaminglayer (lsl)

```python
import lslringbuffer_multithreaded as lbm
from queue import Queue
from threading import Thread
import time

eeg_sig = Queue()
lslringbuffer = lbm.LSLRINGBUFFER(lsl_type='EEG', fs=250, buffer_duration=4.0, num_channels=33)
t1 = Thread(target=lslringbuffer.run, args=(eeg_sig,))
t1.start()
time.sleep(5)

while True:
	data = eeg_sig.get()
```




# viz

The class provides a graphing toolset for visualizing real-time stream in labstreaminglayer (lsl)

```python
from viz import rt_timeseries
streams = rt_timeseries.pylsl.resolve_byprop('name','DummyStream')
eeg_graph = rt_timeseries.Grapher(streams[0],250*10,'k',invert=True)
```




# Running App using iPython

The code that runs the main LSL GUI application

First, start streaming data. If no hardware is available, open another terminal window and generate the dummy stream by typing "python -m start_stream --dummy" in the command line. Switch back to the original terminal window and run the application from the lslbuffer directory by typing the command:

```bash
python -m VersaStream
```