
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

```bash
import lslbuffer as lb
lslobj = lb.LSLBUFFER(stream_type='EEG', buffer_size=4.0)
lslobj.configure()
lslobj.start()
while True:
	data, marker = lslobj.get_data()
    # do something with data and/or break the loop
    lslobj.stop()
```
