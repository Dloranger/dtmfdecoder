# dtmfdecoder
control software for hardware DTMF decoder module for the ICS Control PiRepeater products

This software works with a simple, inexpensive (~$5.00) MT8870 DTMF Decoder Module.   Even though the module specifies it runs at 5vdc, it actually operates just fine using 3.3v parasitic power from the GPIO pins on the PiRepeater controller.

This is the old version that polls the gpio pins for data instead of using interrupts.  it still works, but is a bit more CPU intensive than the interrupt version in the master branch.

