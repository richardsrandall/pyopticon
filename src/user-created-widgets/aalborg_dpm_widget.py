import numpy as np
from collections import defaultdict
from pyopticon import generic_widget
from pyopticon import generic_serial_emulator

import time
import traceback

class AalborgDPMWidget(generic_widget.GenericWidget):
    """ Widget for an Aalborg DPM mass flow meter (MFM).
    This widget controls a single MFM via a serial port.\n
    By default, the gas selection dropdown includes a few gases that the author happened to use.
    Aalborg has many, many gas options in its user manual. You can configure the gas options in the constructor.\n
    In practice, the MFM's sometimes bug out when serial commands are sent directly back-to-back, so we use a short delay between queries/commands that are sent.
    
    One can add a manual calibration curve, though these devices tend to be pretty accurate. This is done by tabulating the commanded flow (i.e., the value sent to 
    the MFM) and the actual flow (according to an external flow meter) at various flow conditions, then feeding the resulting tuples of 
    flows to the constructor for this class.

    :param parent_dashboard: The dashboard object to which this device will be added
    :type parent_dashboard: pyopticon.dashboard.PyOpticonDashboard
    :param name: The name that the widget will be labeled with, and under which its data will be logged, e.g. "Reactor Mass Flow Meter"
    :type name: str
    :param nickname: A shortened nickname that can be used to identify the widget in automation scripts, e.g. "CH4 MFM"
    :type nickname: str
    :param default_serial_port: The name of the default selected serial port, e.g. 'COM9'
    :type default_serial_port: str
    :param default_gas: The default gas that's selected in the dropdown, defaults to 'Ar' for Argon
    :type default_gas: str, optional
    :param gas_options: The list of gas names (strings) that can be selected. Defaults to argon, hydrogen, and methane.
    :type gas_options: list, optional
    :param gas_numbers: The list of gas numbers (integers) corresponding to gas_options according to the Aalborg DPC handbook. Defaults to indices for Ar, H2, and CH4.    
    :type gas_numbers: list, optional
    :param calibration: a tuple containing two tuples of ints or floats with the results of calibrating the MFM. The first should contain a range of flow commands sent to the MFM. The second should contain the result flows according to an external flow meter. (0,0) should be included, as should a value above the highest flow you expect to use. For example, ( (0,10,20,30), (0,11.5,20.7,33.4) ).
    :type calibration: tuple, optional
    """

    def __init__(self,parent_dashboard,name,nickname,default_serial_port,default_gas='Ar',**kwargs):

        # Unpack kwargs
        if 'gas_options' in kwargs.keys():
            if not 'gas_numbers' in kwargs.keys():
                raise Exception("You must pass both gas_options and gas_numbers if you pass one of them to a DPC MFM constructor.")
            gas_options=kwargs['gas_options']
            gas_numbers=kwargs['gas_numbers']
        else:
            gas_options=["Ar","H2","CH4"]
            gas_numbers=(1,13,15)
        if 'calibration' in kwargs.keys():
            self.use_calibrator=True
            self.flows_according_to_meter=kwargs['calibration'][1]
            self.flows_according_to_mfc=kwargs['calibration'][0]
        else:
            self.use_calibrator=False
        
        """ Constructor for an Aalborg DPC mass flow controller widget."""
        # Initialize the superclass with most of the widget functionality
        super().__init__(parent_dashboard,name,nickname,'#66FF00',default_serial_port=default_serial_port,
                         baudrate=9600,update_every_n_cycles=2)
        # Input fields: select gas, mode, setpoint
        self.gas_options=gas_options
        self.gas_numbers=gas_numbers #Indices in the Aalborg MFM list of gases
        self.add_field(field_type='dropdown',name='Gas Selection',
                       label='Select Gas: ', default_value=default_gas, log=True, options=self.gas_options)
        # Output fields: gas status, mode reading, flow reading. move_field is used to make widget more compact.
        self.add_field(field_type='text output',name='Device Gas',label='Actual: ',default_value='None',log=True,column=2,row=3)
        self.add_field(field_type='text output',name='Actual Flow',label='Actual Flow (sccm): ',default_value='None',log=True)

    def on_serial_open(self,success):
        """If serial opened successfully, do nothing; if not, set readouts to 'No Reading'

        :param success: Whether serial opened successfully, according to the return from the on_serial_read method.
        :type success: bool or str
        """
        # If handshake failed, set readouts to 'none'
        if success is not True:
            for f in ('Device Gas','Actual Flow'):
                self.set_field(f,'No Reading')
        else:
            if self.get_field('Device Gas') in self.gas_options:
                self.set_field('Gas Selection',self.get_field('Device Gas')) #Set default mode to be the device's current mode

    def on_serial_query(self):
        """Send two queries to the serial device asking for the gas selection, mode, setpoint, and actual flow rate.
        Mode refers to open, closed, or setpoint.
        """
        s = self.get_serial_object()
        s.reset_input_buffer()
        queries = [b'G\r',b'FM\r'] #Gas, flow rate)
        self.send_via_queue(queries[0],50)
        self.send_via_queue(queries[1],350)

    def on_serial_read(self):
        """Parse the responses from the previous 2 serial queries and update the display. Return True if valid and an error string if not.

        :return: True if all 2 responses were of the expected format, an error string otherwise.
        :rtype: bool or str
        """
        lines=self.get_serial_object().readlines()
        try:
            # Parse the Gas data
            gas = lines[0]
            gas = gas[gas.index(b':')+1:]
            gas = gas[gas.index(b',')+1:gas.index(b'\r')]
            self.set_field('Device Gas',gas.decode('ascii'))
            # Parse the flow data
            flow_status = lines[1]
            flow_start = flow_status.index(b">")
            flow_end = flow_status.index(b"\r")
            flow_status = flow_status[flow_start+1:flow_end]
            flow_value = (max(0,float(flow_status)))
            if self.use_calibrator:
                flow_value = np.interp(flow_value,
                                           self.flows_according_to_mfc,self.flows_according_to_meter)# Serial reports a flow acc. to the MFM; need to display actual 
            flow_str = "{:.1f}".format(flow_value)
            self.set_field('Actual Flow',flow_str)
        except Exception as e:
            #print(traceback.format_exc())
            for f in ('Device Gas','Actual Flow'):
                self.set_field(f,'Read Error')
            fail_message=("Bad response in Aalborg MFM, in one of: "+str(lines))
            return fail_message
        return True
            
    def on_serial_close(self):
        """When serial is closed, set all readouts to 'None'."""
        for f in ('Device Gas','Actual Flow'):
            self.set_field(f,'None')
            
    def on_confirm(self):
        """When 'confirm' is pressed, send the appropriate commands to the MFM.
        Prints warnings to console if the entered parameters are invalid.
        """
        # Update the MFM gas:
        gas = self.get_field('Gas Selection')
        g = gas
        if not(gas in self.gas_options):
            print("\"Confirm\" pressed with no/invalid gas option selected.")
            return
        gas = str(self.gas_numbers[self.gas_options.index(gas)]).encode('ascii')
        gas_cmd=(b'G,'+gas+b'\r')
        self.send_via_queue(gas_cmd,100)
        print("MFM '"+str(self.name)+"' set to gas "+g)

    def construct_serial_emulator(self):
        """Get the serial emulator to use when we're testing in offline mode.

        :return: An Aalborg DPC serial emulator object.
        :rtype: aalborg_dpm_widget.AalborgDPCSerialEmulator"""
        return AalborgDPMSerialEmulator()

class AalborgDPMSerialEmulator(generic_serial_emulator.GenericSerialEmulator):
    """Serial emulator to allow offline testing of dashboards containing Aalborg DPM mass flow meters.
    Acts as a Pyserial Serial object for the purposes of the program, implementing a few of the same methods. Has a fake 'input buffer' 
    where responses to queries from a fake 'MFM' are stored.\n
    Serial queries are answered with a fixed gas (Ar) and a random actual flow (100-104 sccm).
    """
    
    def __init__(self):
        """Create a new serial emulator for an Aalborg DPC."""
        self.output_buffer = []
        self.setpoint=100

    def reset_input_buffer(self):
        """Reset the serial buffer, as if this were a Pyserial Serial object."""
        self.output_buffer = []

    def write(self,value):
        """Write to this object as if it were a Pyserial Serial object. Adds appropriate responses to a fake input buffer.

        :param value: The string to write, encoded as ascii bytes.
        :type value: bytes"""
        queries = (b'G\r',b'V,M\r',b'SP\r',b'FM\r')
        if value not in queries:
            self.output_buffer.append(b'IDK\r')#Nonsense answer
        setpoint_str = 'SP:'+str(self.setpoint)+'\r'
        reading_str = '>'+str(self.setpoint+np.random.randint(0,5))+'\r'
        responses = (b'G:1,AR\r',b'VM:A\r',setpoint_str.encode('ascii'),reading_str.encode('ascii'))
        self.output_buffer.append((responses[queries.index(value)]))

    def readline(self):
        """Reads a response from the fake input buffer as if this were a Pyserial Serial object.

        :return: The next line in the fake input buffer.
        :rtype: str"""
        return self.output_buffer.pop(0)

    def readlines(self):
        """Reads all responses from the fake input buffer as if this were a Pyserial Serial object.

        :return: A list of lines in the fake input buffer.
        :rtype: list"""
        out = list(self.output_buffer)
        self.output_buffer = []
        return out

    def close(self):
        """Close the object as if this were a Pyserial Serial object."""
        pass

