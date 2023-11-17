import numpy as np
from pymodbus.client import ModbusSerialClient
import math

from pyopticon import generic_widget

class CellkraftHumidifierWidget(generic_widget.GenericWidget):
    """ This widget represents a CellKraft P10 flow-through humidifier.

    :param parent_dashboard: The dashboard object to which this device will be added
    :type parent_dashboard: pyopticon.dashboard.PyOpticonDashboard
    :param name: The name that the widget will be labeled with, and under which its data will be logged, e.g. "Methane Mass Flow Controller"
    :type name: str
    :param nickname: A shortened nickname that can be used to identify the widget in automation scripts, e.g. "CH4 MFC"
    :type nickname: str
    
    """

    def __init__(self,parent_dashboard,name,nickname,default_serial_port):
        """ Constructor for a humidifier widget."""
        # Initialize the superclass with most of the widget functionality
        super().__init__(parent_dashboard,name,nickname,'#000088',default_serial_port=default_serial_port,update_every_n_cycles=2)
        # Add a readout field
        self.add_field(field_type='text output', name='Humidity (vol %)',
                       label='Humidity (vol %): ', default_value='No Reading', log=True)
        self.add_field(field_type='text input', name='Setpoint Entry (vol %)',
                       label='Setpoint Entry (vol %): ', default_value='0.00', log=True)
        self.add_field(field_type='text output', name='Actual Setpoint (vol %)',
                       label='Actual Setpoint (vol %): ', default_value='No Reading', log=True)
        self.field_names=('Humidity (vol %)','Actual Setpoint (vol %)')


    def build_serial_object(self):
        """Builds a modbus object."""
        return ModbusSerialClient(self.serial_selected.get(),baudrate=19200)

    def on_serial_open(self,success):
        """If the device initialized successfully, do nothing; if not, set its readout to 'No Reading'

        :param success: Whether serial opened successfully, according to the return from the on_serial_read method.
        :type success: bool"""
        if not success:
            for f in self.field_names:
                self.set_field(f,'No Reading')

    def on_serial_query(self):
        """"Nothing done here; all queries are done with blocking code in on_serial_read"""
        pass

    def on_serial_read(self):
        """Query the device and update the fields with the responses."""
        rh = self.serial_object.read_holding_registers(address=1090, count=1, unit=1)
        rh=(float(rh.registers[0])/100)
        t = self.serial_object.read_holding_registers(address=1086, count=1, unit=1)
        t=(float(t.registers[0])/100)
        #vol_perc_sat = 0.0231*math.exp((40700/8.31)*((1/(t+273))-(1/373)))
        vol_perc_sat = (10**(8.07131-1730.63/(233.426+t)))/760
        #print("Temp "+str(t)+"C gives max vol % "+str(vol_perc_sat))
        vp = round(vol_perc_sat*rh,3)
        self.set_field('Humidity (vol %)',str(vp))
        sp = self.serial_object.read_holding_registers(address=104, count=1, unit=1)
        sp=(float(sp.registers[0])/100)
        self.set_field('Actual Setpoint (vol %)',str(sp))

    def on_confirm(self):
        """Send a command to the device"""
        setpoint = float(self.get_field('Setpoint Entry (vol %)'))
        cmd = (max(0,int(setpoint*100)))
        self.serial_object.write_register(address=104,value=cmd)

    def on_serial_close(self):
        """When serial is closed, set all readouts to 'None'."""
        for f in self.field_names:
            self.set_field(f,'No Reading')
        self.serial_object=None

    def construct_serial_emulator(self):
        """Emulating a modbus connection seems kind of annoying, so I'm not going to do it. This widget won't work in offline mode.
        
        :return: None
        :rtype: NoneType
        """
        return None


    
