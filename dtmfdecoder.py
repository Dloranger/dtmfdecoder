#!/usr/bin/python
# Copyright (c) 2019 John Tetreault (WA1OKB)
#
# Permission is hereby granted for the use, free of charge, to
# any person obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software, and
# to permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import sys
import subprocess
import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

#Export the GPIO pins we're going to use
for x in range (498, 504):
        subprocess.call("echo " + str(x) + " > /sys/class/gpio/export", shell=True)
subprocess.call("echo 12 > /sys/class/gpio/export", shell=True)
subprocess.call("echo both > /sys/class/gpio/gpio502/edge", shell=True)
subprocess.call("echo out > " + str(GPIOPath) + str(Vcc) + "/direction", shell=True)
GPIO.setup(12, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#Setup default variables based on pinout of DTMF decoder board
IRQ = 12		#GPIO Expander interrupt pin from /boot/config.txt
Vcc = "gpio503"		#3.3vdc, just setting the GPIO high provides sufficient power to run the board
Q1 = "gpio498"    	#DTMF = DTMF + 1
Q2 = "gpio499"		#DTMF = DTMF + 2
Q3 = "gpio500"		#DTMF = DTMF + 4
Q4 = "gpio501"		#DTMF = DTMF + 8
STQ2 = "gpio502" 	#Normally High, goes low when tone detected, then back high once tone stops.
GPIOPath = "/sys/class/gpio/"

#Get DTMF_PTY path from supplemental config file
svxlinkvars = {}
with open("/etc/svxlink/svxlink.d/dtmfdecoder.conf") as myfile:
        for line in myfile:
                name, var = line.partition("=")[::2]
                svxlinkvars[name.strip()] = var[:-1]
DTMFPty = str(svxlinkvars["DTMF_PTY"])


#Define function to read individual GPIO pins
def getvalue(pin):
	cmd = "cat " + GPIOPath + pin + "/value"
	bit = subprocess.check_output(cmd, shell = True)
	return int(bit)

#Define function to convert binary coded decimal to keypress
def getDigit(Q1,Q2,Q3,Q4):	#Callback when interrupt goes low
	print "received interrupt"    #for debugging, will remove this line once we get the interrupt working
	if getvalue(502):
		bits = [getvalue(Q1),getvalue(Q2),getvalue(Q3),getvalue(Q4)]
		dtmf = ["D","1","2","3","4","5","6","7","8","9","0","*","#","A","B","C"]
		code = 0
		code = (bits[0] * 1) + (bits[1] * 2) + (bits[2] * 4) + (bits[3] * 8)
		Key = str(dtmf[code])
		print str(Key)
	        subprocess.call('echo "' + str(Key) + '" > ' + str(DTMFPty), shell=True)    #Send digit to svxlink
		return
	else:
		subprocess.call('echo " " > ' + str(DTMFPty), shell=True)	#Clear digit sent to svxlink when tones end
		return

GPIO.add_event_detect(12, GPIO.BOTH, callback=getDigit, bouncetime=100)   #Capture interrupt event

#Initialize the DTMF Decoder board by power cycling the Vcc pin
subprocess.call('echo 0 > ' + GPIOPath + Vcc + '/value', shell = True)
time.sleep(1)
subprocess.call('echo 1 > ' + GPIOPath + Vcc + '/value', shell = True)

#Main program loop
while True:

	try:
		time.sleep(1)
	except KeyboardInterrupt:
		GPIO.cleanup()
		sys.exit(1)
GPIO.cleanup()

