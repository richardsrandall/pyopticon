import numpy as np
import time
import traceback
from .thorlabs.TLPM import TLPM
import math
from datetime import datetime
from ctypes import cdll,c_long, c_ulong, c_uint32,byref,create_string_buffer,c_bool,c_char_p,c_int,c_int16,c_double, sizeof, c_voidp

# Test the superclass genericWidget
from .. import generic_widget

class ThorlabsLightMeterWidget(generic_widget.GenericWidget):
    """ This widget represents a Thorlabs optical power meter, e.g. a PM100D. The Thorlabs driver library (one .py and two .dll's) needs to be
    in a folder labeled 'thorlabs' next to the widget. You may have to go into TLPM.py and edit the .dll file paths (listed as strings) if it's having trouble loading them.

    :param parent_dashboard: The dashboard object to which this device will be added
    :type parent_dashboard: richardview.dashboard.RichardViewDashboard
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
        super().__init__(parent_dashboard,name,nickname,'#CC0044',use_serial=False,update_every_n_cycles=1)
        # Add a readout field
        self.add_field(field_type='text output', name='Irradiance (mW/cm2)',
                       label='Irradiance (mW/cm2): ', default_value='No Reading', log=True)
        self.field_names=["Irradiance (mW/cm2)"]
        self.scale_factor = scale_factor
        self.wavelength=wavelength
        self.device_index=device_index

    def on_failed_serial_open(self):
        """If serial open failed, set readouts to 'No Reading'
        """
        # If handshake failed, set readout to 'none'
        self.set_field('Irradiance (mW/cm2)','No Reading',hush_warning=True)

    def on_handshake(self):
        """Connect to the power meter and conduct a handshake."""

        if self.parent_dashboard.offline_mode:
            self.on_update()
            return
        
        # Find the only LPM connected and assume it's the correct device.
        # Bunch of mumbo-jumbo...
        tlPM = TLPM()
        deviceCount = c_uint32()
        tlPM.findRsrc(byref(deviceCount))
        resourceName = create_string_buffer(1024)
        tlPM.getRsrcName(self.device_index, resourceName)
        tlPM.close()
        tlPM = TLPM()
        tlPM.open(resourceName, c_bool(True), c_bool(True))

        # Set wavelength in nm
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

        # Try to talk to it.
        self.on_update()

            
    def on_update(self):
        """Query the device and update the fields with the responses."""
        if (not self.handshake_was_successful) or ((self.serial_object == None) and not (self.parent_dashboard.offline_mode)):
            return
        if not self.parent_dashboard.offline_mode:
            power =  c_double()
            self.serial_object.measPower(byref(power))
        else:
            power = c_double(0.001*(5+0.1*np.random.randint(0,5)))
        irrad = power.value*self.scale_factor*1000/1.00
        self.set_field('Irradiance (mW/cm2)',float(round(irrad,2)))
        # No return means a successful handshake

    def on_serial_close(self):
        """When serial is closed, set all readouts to 'None'."""
        if self.parent_dashboard.offline_mode:
            return
        for f in self.field_names:
            self.set_field(f,'No Reading')
        if self.handshake_was_successful and (self.serial_object is not None):
            self.serial_object.close()
        self.serial_object = None

