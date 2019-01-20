from  freshroastsr700 import *
import sys
import time
import logging

from multiprocessing import Process, Value, Array


from Phidget22.Devices.TemperatureSensor import *
from Phidget22.PhidgetException import *
from Phidget22.Phidget import *
from freshroastsr700_phidget.PhidgetHelperFunctions import *


class PhidgetTemperature(object):
    def __init__(self):
        try:
            self.ch = TemperatureSensor()
        except PhidgetException as e:
            sys.stderr.write("Runtime Error -> Creating TemperatureSensor: \n\t")
            DisplayError(e)
            raise
        except RuntimeError as e:
            sys.stderr.write("Runtime Error -> Creating TemperatureSensor: \n\t" + e)
            raise
        print("\nOpening and Waiting for Attachment...")

        try:
            self.ch.openWaitForAttachment(5000)
        except PhidgetException as e:
            PrintOpenErrorMessage(e, self.ch)
            raise EndProgramSignal("Program Terminated: Open Failed")

        print("Ready!")

    def getTemperature(self,fahrenheit=False):

        if fahrenheit:
            return ( self.ch.getTemperature() * 9/5.0) + 32

        else:
            return self.ch.getTemperature()


    def closeConnection(self):
        return self.ch.close()

class SR700Phidget(freshroastsr700):


    def __init__(self,use_phidget_temp, *args, **kwargs):

        self._current_temp_phidget=Value('d', 0.0)
        
        if use_phidget_temp:
           self._use_phidget_temp=Value('d', 1.0)
        else:
           self._use_phidget_temp=Value('d', 0.0)

        super(SR700Phidget, self).__init__(*args, **kwargs)

    @property
    def current_temp_phidget(self):

        return self._current_temp_phidget.value

    @current_temp_phidget.setter
    def current_temp_phidget(self, value):
        #if value not in range(150, 551):
        #    raise exceptions.RoasterValueError

        self._current_temp_phidget.value=value



    def _comm(self, thermostat=False,
        kp=1, ki=1, kd=2,
        heater_segments=8, ext_sw_heater_drive=False,
        update_data_event=None):
        """Do not call this directly - call auto_connect(), which will spawn
        comm() for you.

        This is the main communications loop to the roaster.
        whenever a valid packet is received from the device, if an
        update_data_event is available, it will be signalled.

        Args:
            thermostat (bool): thermostat mode.
            if set to True, turns on thermostat mode.  In thermostat
            mode, freshroastsr700 takes control of heat_setting and does
            software PID control to hit the demanded target_temp.

            ext_sw_heater_drive (bool): enable direct control over the internal
            heat_controller object.  Defaults to False. When set to True, the
            thermostat field is IGNORED, and assumed to be False.  Direct
            control over the software heater_level means that the
            PID controller cannot control the heater.  Since thermostat and
            ext_sw_heater_drive cannot be allowed to both be True, this arg
            is given precedence over the thermostat arg.

            kp (float): Kp value to use for PID control. Defaults to 0.06.

            ki (float): Ki value to use for PID control. Defaults to 0.0075.

            kd (float): Kd value to use for PID control. Defaults to 0.01.

            heater_segments (int): the pseudo-control range for the internal
            heat_controller object.  Defaults to 8.

            update_data_event (multiprocessing.Event): If set, allows the
            comm_process to signal to the parent process that new device data
            is available.

        Returns:
            nothing
        """
        # since this process is started with daemon=True, it should exit
        # when the owning process terminates. Therefore, safe to loop forever.
        ph=PhidgetTemperature()
        
        use_phidget_temp=self._use_phidget_temp.value
        if use_phidget_temp:
            logging.info('Using Phidget temp kp: %f ki: %f kd: %f' % (kp,ki,kd))
        else:
            logging.info('Not using Phidget temp kp: %f ki: %f kd: %f' % (kp,ki,kd))
            #kp=0.06
            #ki=0.0075
            #kd=0.01
            

        while not self._teardown.value:

            logging.info('Starting comm process')

            # waiting for command to attempt connect
            # print( "waiting for command to attempt connect")
            while self._attempting_connect.value == self.CA_NONE:
                time.sleep(0.25)
                if self._teardown.value:
                    break
            # if we're tearing down, bail now.
            if self._teardown.value:
                break

            # we got the command to attempt to connect
            # change state to 'attempting_connect'
            self._connect_state.value = self.CS_ATTEMPTING_CONNECT
            # attempt connection
            if self.CA_AUTO == self._attempting_connect.value:
                # this call will block until a connection is achieved
                # it will also set _connect_state to CS_CONNECTING
                # if appropriate
                if self._auto_connect():
                    # when we unblock, it is an indication of a successful
                    # connection
                    self._connected.value = 1
                    self._connect_state.value = self.CS_CONNECTED
                else:
                    # failure, normally due to a timeout
                    self._connected.value = 0
                    self._connect_state.value = self.CS_NOT_CONNECTED
                    # we failed to connect - start over from the top
                    # reset flag
                    self._attempting_connect.value = self.CA_NONE
                    continue

            elif self.CA_SINGLE_SHOT == self._attempting_connect.value:
                # try once, now, if failure, start teh big loop over
                try:
                    self._connect()
                    self._connected.value = 1
                    self._connect_state.value = self.CS_CONNECTED
                except exceptions.RoasterLookupError:
                    self._connected.value = 0
                    self._connect_state.value = self.CS_NOT_CONNECTED
                if self._connect_state.value != self.CS_CONNECTED:
                    # we failed to connect - start over from the top
                    # reset flag
                    self._attempting_connect.value = self.CA_NONE
                    continue
            else:
                # shouldn't be here
                # reset flag
                self._attempting_connect.value = self.CA_NONE
                continue

            # We are connected!
            # print( "We are connected!")
            # reset flag right away
            self._attempting_connect.value = self.CA_NONE

            # Initialize PID controller if thermostat function was specified at
            # init time
            pidc = None
            heater = None
            if(thermostat):

                pidc = pid.PID(kp, ki, kd,
                               Output_max=heater_segments,
                               Output_min=0
                               )
            if thermostat or ext_sw_heater_drive:
                heater = heat_controller(number_of_segments=heater_segments)

            read_state = self.LOOKING_FOR_HEADER_1
            r = []
            write_errors = 0
            read_errors = 0
            while not self._disconnect.value:
                start = datetime.datetime.now()
                # write to device
                if not self._write_to_device():
                    logging.error('comm - _write_to_device() failed!')
                    write_errors += 1
                    if write_errors > 3:
                        # it's time to consider the device as being "gone"
                        logging.error('comm - 3 successive write '
                                      'failures, disconnecting.')
                        self._disconnect.value = 1
                        continue
                else:
                    # reset write_errors
                    write_errors = 0

                # read from device
                try:
                    while self._ser.in_waiting:
                        _byte = self._ser.read(1)
                        read_state, r, err = (
                            self._process_reponse_byte(
                                read_state, _byte, r, update_data_event))
                except IOError:
                    # typically happens when device is suddenly unplugged
                    logging.error('comm - read from device failed!')
                    read_errors += 1
                    if write_errors > 3:
                        # it's time to consider the device as being "gone"
                        logging.error('comm - 3 successive read '
                                      'failures, disconnecting.')
                        self._disconnect.value = 1
                        continue
                else:
                    read_errors = 0

                # next, drive SW heater when using
                # thermostat mode (PID controller calcs)
                # or in external sw heater drive mode,
                # when roasting.
                if thermostat or ext_sw_heater_drive:

                    #if use_phidget_temp:
                    self.current_temp_phidget=int( ph.getTemperature(fahrenheit=True))

                    if 'roasting' == self.get_roaster_state():
                        if heater.about_to_rollover():
                            # it's time to use the PID controller value
                            # and set new output level on heater!
                            if ext_sw_heater_drive:
                                # read user-supplied value
                                heater.heat_level = self._heater_level.value
                            else:
                                # thermostat



                                #this will use the phidget
                                if use_phidget_temp:
                                    #logging.info('Using Phidget')
                                    output = pidc.update(
                                        self.current_temp_phidget,self.target_temp )
                                else:
                                    logging.info('Using Internal Temp')
                                    output = pidc.update(
                                        self.current_temp, self.target_temp)

                                logging.info('SR700 temp: %d Phidget Temp:%d Target Temp:%d Heat:%d Using Phidget Temp:%d' % (self.current_temp,
                                    self.current_temp_phidget,
                                    self.target_temp,
                                    output, use_phidget_temp))

                                heater.heat_level = output
                                # make this number visible to other processes...
                                self._heater_level.value = heater.heat_level
                        # read bang-bang heater output array element & apply it
                        if heater.generate_bangbang_output():
                            # ON
                            self.heat_setting = 3
                        else:
                            # OFF
                            self.heat_setting = 0
                    else:
                        # for all other states, heat_level = OFF
                        heater.heat_level = 0
                        # make this number visible to other processes...
                        self._heater_level.value = heater.heat_level
                        self.heat_setting = 0

                # calculate sleep time to stick to 0.25sec period
                comp_time = datetime.datetime.now() - start
                sleep_duration = 0.25 - comp_time.total_seconds()
                if sleep_duration > 0:
                    time.sleep(sleep_duration)

            self._ser.close()
            # reset disconnect flag
            self._disconnect.value = 0
            # reset connection values
            self._connected.value = 0
            self._connect_state.value = self.CS_NOT_CONNECTED
            # print("We are disconnected.")

            if use_phidget_temp:
                ph.closeConnection()