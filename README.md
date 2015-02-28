# dtmf
Dual Tone Multi Frequency generator


This module contains a DTMF class that encapsulates a sequence of the form [tone, duration]. This sequence can be converted to raw data that can be saved to a wav.

The idea is that DTMF acts as an object that encapsulates a sequence that can be operated on. Adding support for different file formats should be a matter of compressing that raw data. 
