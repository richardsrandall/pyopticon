import numpy as np
from pymodbus.client import ModbusSerialClient
import math
from datetime import datetime
from ctypes import cdll,c_long, c_ulong, c_uint32,byref,create_string_buffer,c_bool,c_char_p,c_int,c_int16,c_double, sizeof, c_voidp
from .thorlabs.TLPM import TLPM
import time

from pyopticon import generic_widget

class ThorlabsOpticalPowerMeterWidget(generic_widget.GenericWidget):
    """ This widget represents a Thorlabs optical power meter, e.g. a PM100D. The Thorlabs driver files (one .py and two .dll's) aren't included here and need to be
    in a folder labeled 'thorlabs' next to the widget. You may have to go into TLPM.py and edit the .dll file paths (listed as strings) if it's having trouble loading them.

    Googling 'Thorlabs TLPM.py' should let you find the driver files. They are included with downloads of Thorlabs' monitoring software. This document has some details that may help: https://www.thorlabs.com/software/MUC/OPM/v2.1/TL_OPM_V2.1_web-secured.pdf

    :param parent_dashboard: The dashboard object to which this device will be added
    :type parent_dashboard: pyopticon.dashboard.PyOpticonDashboard
    :param name: The name that the widget will be labeled with, and under which its data will be logged, e.g. "Methane Mass Flow Controller"
    :type name: str
    :param nickname: A shortened nickname that can be used to identify the widget in automation scripts, e.g. "CH4 MFC"
    :type nickname: str
    :param wavelength: The wavelength of light assumed, in nm. Relevant for photodiode sensors.
    :type wavelength: int
    :param scale_factor: A float constant by which to multiply the measured power to get an irradiance - usually 1/(collector area).
    :type scale_factor: float
    :param device_index: The index of the Thorlabs device this widget represents, according to the Thorlabs driver's list of compatible devices. Defaults to 0, but you may set to 1, 2, etc. if you have more than one Thorlabs power meter connected to your computer. With multiple devices, find the indices by trial and error.
    :type device_index: int
    """

    def __init__(self,parent_dashboard,name,nickname,wavelength,scale_factor,device_index=0):
        """ Constructor for a power meter widget."""
        # Initialize the superclass with most of the widget functionality
        super().__init__(parent_dashboard,name,nickname,'#CC0044',no_serial=True,update_every_n_cycles=1)
        # Add a readout field
        self.add_field(field_type='text output', name='Irradiance (mW/cm2)',
                       label='Irradiance (mW/cm2): ', default_value='No Reading', log=True)
        self.field_names=["Irradiance (mW/cm2)"]
        self.scale_factor = scale_factor
        self.wavelength=wavelength
        self.device_index=device_index


    def build_serial_object(self):
        """Builds a Thorlabs optical power meter object."""
        # Find the only LPM connected and assume it's the correct device.
        # Bunch of mumbo-jumbo...
        self.connect_succeeded=False
        try:
            tlPM = TLPM()
            deviceCount = c_uint32()
            tlPM.findRsrc(byref(deviceCount))
            resourceName = create_string_buffer(1024)
            tlPM.getRsrcName(self.device_index, resourceName)
            tlPM.close()
            tlPM = TLPM()
            tlPM.open(resourceName, c_bool(True), c_bool(True))

            # Set wavelength in nm.
            wavelength = c_double(self.wavelength)
            tlPM.setWavelength(wavelength)

            # Enable auto-range mode.
            # 0 -> auto-range disabled
            # 1 -> auto-range enabled
            tlPM.setPowerAutoRange(c_int16(1))

            # Set power unit to Watt.
            # 0 -> Watt
            # 1 -> dBm
            tlPM.setPowerUnit(c_int16(0))
            self.serial_object=tlPM
            self.connect_succeeded=True
            return tlPM
        except Exception as e:
            print(e)

    def on_serial_open(self,success):
        """If the device initialized successfully, do nothing; if not, set its readout to 'No Reading'

        :param success: Whether serial opened successfully, according to the return from the on_serial_read method.
        :type success: bool"""
        if not success:
            for f in self.field_names:
                self.set_field(f,'No Device Found')

    def on_serial_query(self):
        """"Nothing done here; all queries are done with blocking code in on_serial_read"""
        pass

    def on_serial_read(self):
        """Query the device and update the fields with the responses."""
        if not self.connect_succeeded: #We track this because no_serial objects don't have a built-in way of tracking whether serial succeeded or not
            return 'Connection Failed'
        power =  c_double()
        self.serial_object.measPower(byref(power))
        irrad = power.value*self.scale_factor*1000/1.00
        self.set_field('Irradiance (mW/cm2)',float(round(irrad,2)))
        # No return means a successful handshake
        
    def on_serial_close(self):
        """When serial is closed, set all readouts to 'None'."""
        for f in self.field_names:
            self.set_field(f,'No Reading')
        if self.connect_succeeded and self.serial_object is not None:
            self.serial_object.close()
        self.connect_succeeded=False

    def construct_serial_emulator(self):
        """It'd be hard to make an emulator for a 3rd-party library. This widget won't work in offline mode.
        
        :return: None
        :rtype: NoneType
        """
        return None


    
