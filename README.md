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
