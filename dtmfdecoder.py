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

## Note  In order for interrupts to work correctly, the following line in /boot/config.txt
## needs to be changed
##	dtoverlay=mcp23017,addr=0x20,gpiopin=12
## change it to
##	dtoverlay=mcp23017,addr-0x20,gpiopin=6
## Then reboot the system.  This is an unused gpio pin on the pi.  The reason for the change is the
## hardware overlay locks out interrupt detection on the real gpio pin, 12.
## So by doing this, we trick the hardware overlay into not locking out interrupts on gpiopin 12

import sys
import subprocess
import time
import RPi.GPIO as GPIO
import datetime
GPIO.setmode(GPIO.BCM)

#Setup default variables based on pinout of DTMF decoder board
IRQ = "gpio12"		#GPIO Expander interrupt pin
Vcc = "gpio503"		#3.3vdc, just setting the GPIO high provides sufficient power to run the board
Q1 = "gpio498"    	#DTMF = DTMF + 1
Q2 = "gpio499"		#DTMF = DTMF + 2
Q3 = "gpio500"		#DTMF = DTMF + 4
Q4 = "gpio501"		#DTMF = DTMF + 8
STQ2 = "gpio502" 	#Normally High, goes low when tone detected, then back high once tone stops.
GPIOPath = "/sys/class/gpio/"

#Export the GPIO pins on bank A of the MCP23017 GPIO expander
for x in range (496, 504):
	subprocess.call("echo " + str(x) + " > /sys/class/gpio/export", shell=True)
subprocess.call("echo 12 > /sys/class/gpio/export", shell=True)
subprocess.call("echo 1 > /sys/class/gpio/gpio12/active_low", shell=True)
subprocess.call("echo falling > /sys/class/gpio/" + STQ2 + "/edge", shell=True)
subprocess.call("echo out > /sys/class/gpio/" + Vcc + "/direction", shell=True)
GPIO.setup(12, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#Get DTMF_PTY path from supplemental config file
svxlinkvars = {}
with open("/etc/svxlink/svxlink.d/dtmfdecoder.conf") as myfile:
        for line in myfile:
                name, var = line.partition("=")[::2]
                svxlinkvars[name.strip()] = var[:-1]
DTMFPty = str(svxlinkvars["DTMF_PTY"])

#Define function to read individual GPIO pins
def getvalue(pin):
	cmd = "cat " + GPIOPath + str(pin) + "/value"
	bit = subprocess.check_output(cmd, shell = True)
	return int(bit)

#Define function to convert binary coded decimal to keypress
def getDigit():	#Callback when interrupt goes low
	if not getvalue(STQ2):														#STQ2 is low when tone is detected
		bits = [getvalue(Q1),getvalue(Q2),getvalue(Q3),getvalue(Q4)]								#Get binary coded decimal from MT8870
		dtmf = ["D","1","2","3","4","5","6","7","8","9","0","*","#","A","B","C"]						#Array of possible key presses
		code = 0														#zero out any previous attempts
		code = (bits[0] * 1) + (bits[1] * 2) + (bits[2] * 4) + (bits[3] * 8)							#Convert binary coded decimal to decimal
		Key = str(dtmf[code])													#Convert decimal to dtmf digit pressed from array
		logentry = datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Y") + ": MT8870 DTMF Decoder: digit=" + str(Key)	#Generate log entry
		subprocess.call('echo "' + logentry + '" >> /var/log/svxlink', shell=True)   						#Log successful hardware DTMF detection to SVXLink log
		subprocess.call('echo "' + str(Key) + '" > ' + str(DTMFPty), shell=True)						#Send the digit to svxlink
	else:
		subprocess.call('echo  " " > ' + str(DTMFPty), shell=True)								#Clear digit sent to svxlink when tones end and STQ2 goes high
	return

callback = lambda self : getDigit()
GPIO.add_event_detect(12, GPIO.RISING, callback=callback, bouncetime=100)   								#Capture interrupt event

#Initialize the DTMF Decoder board by power cycling the Vcc pin
subprocess.call('echo 0 > ' + GPIOPath + Vcc + '/value', shell = True)
time.sleep(1)
subprocess.call('echo 1 > ' + GPIOPath + Vcc + '/value', shell = True)
getvalue(STQ2)																#Clear interrupts from initial setup by reading pin


#Main program loop
while True:

	try:
		time.sleep(10)
	except KeyboardInterrupt:
		GPIO.cleanup()
		sys.exit(1)
GPIO.cleanup()

