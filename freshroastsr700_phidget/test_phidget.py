from Phidget22.Devices.TemperatureSensor import *
from Phidget22.PhidgetException import *
from Phidget22.Phidget import *
from freshroastsr700_phidget.PhidgetHelperFunctions import *
import logging
import sys

import time

class PhidgetTemperature(object):
    def __init__(self,hub_port=0,hub_channel=1,serial_number=-1,use_hub=False):

        self.use_hub=use_hub
        self.hub_port=hub_port
        self.hub_channel=hub_channel

        try:
            self.ch = TemperatureSensor()
            self.ch.setDeviceSerialNumber(serial_number)
            if use_hub:
                self.ch.setHubPort(hub_port)
                self.ch.setIsHubPortDevice(1)
                self.ch.setChannel(hub_channel)
                print('HUB, PORT:%d CHANNEL: %d' %(hub_port,hub_channel))
        except PhidgetException as e:
            sys.stderr.write("Runtime Error -> Creating TemperatureSensor: \n\t")
            DisplayError(e)
            self.ch.close()
            raise
        except RuntimeError as e:
            sys.stderr.write("Runtime Error -> Creating TemperatureSensor: \n\t" + e)
            self.ch.close()
            raise

        logging.info("Phidget: Opening and Waiting for Attachment...")

        try:
            self.ch.openWaitForAttachment(5000)
        except PhidgetException as e:
            PrintOpenErrorMessage(e, self.ch)
            self.ch.close()
            raise EndProgramSignal("Program Terminated: Open Failed")
        time.sleep(1)
        logging.info("Phidget: Ready!")

    def getTemperature(self,fahrenheit=False):


        if fahrenheit:
            return ( self.ch.getTemperature() * 9/5.0) + 32

        else:
            return self.ch.getTemperature()


    def closeConnection(self):
        return self.ch.close()


pt=PhidgetTemperature(hub_port=0,hub_channel=1,serial_number=-1,use_hub=True)

for i in range(10):
    pt.getTemperature(fahrenheit=True)

    print('TEMP: ',pt.getTemperature())
    time.sleep(1)

pt.closeConnection()
