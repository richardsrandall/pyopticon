import numpy as np
from collections import defaultdict
from .. import generic_widget

import time
import traceback

class AalborgDPCWidget(generic_widget.GenericWidget):
    """ Widget for an Aalborg DPC mass flow controller (MFC).
    This widget controls a single MFC via a serial port.\n
    By default, the gas selection dropdown includes a few gases that the author happened to use.
    Aalborg has many, many gas options in its user manual. You can configure the gas options in the constructor.\n
    In practice, the MFC's sometimes bug out when serial commands are sent directly back-to-back, so we use a short delay between queries/commands that are sent.
    
    One can add a manual calibration curve, though these devices tend to be pretty accurate. This is done by tabulating the commanded flow (i.e., the value sent to 
    the MFC) and the actual flow (according to an external flow meter) at various flow conditions, then feeding the resulting tuples of 
    flows to the constructor for this class.

    :param parent_dashboard: The dashboard object to which this device will be added
    :type parent_dashboard: richardview.dashboard.RichardViewDashboard
    :param name: The name that the widget will be labeled with, and under which its data will be logged, e.g. "Methane Mass Flow Controller"
    :type name: str
    :param nickname: A shortened nickname that can be used to identify the widget in automation scripts, e.g. "CH4 MFC"
    :type nickname: str
    :param default_serial_port: The name of the default selected serial port, e.g. 'COM9'
    :type default_serial_port: str
    :param default_gas: The default gas that's selected in the dropdown, defaults to 'Ar' for Argon
    :type default_gas: str, optional
    :param gas_options: The list of gas names (strings) that can be selected. Defaults to argon, hydrogen, and methane.
    :type gas_options: list, optional
    :param gas_numbers: The list of gas numbers (integers) corresponding to gas_options according to the Aalborg DPC handbook. Defaults to indices for Ar, H2, and CH4.    
    :type gas_numbers: list, optional
    :param calibration: a tuple containing two tuples of ints or floats with the results of calibrating the MFC. The first should contain a range of flow commands sent to the MFC. The second should contain the result flows according to an external flow meter. (0,0) should be included, as should a value above the highest flow you expect to use. For example, ( (0,10,20,30), (0,11.5,20.7,33.4) ).
    :type calibration: tuple, optional
    """

    def __init__(self,parent_dashboard,name,nickname,default_serial_port,default_gas='Ar',**kwargs):

        # Unpack kwargs
        if 'gas_options' in kwargs.keys():
            if not 'gas_numbers' in kwargs.keys():
                raise Exception("You must pass both gas_options and gas_numbers if you pass one of them to a DPC MFC constructor.")
            gas_options=kwargs['gas_options']
            gas_numbers=kwargs['gas_numbers']
        else:
            gas_options=["Ar","H2","CH4","N2","O2"]
            gas_numbers=(1,13,15,3,4)
        if 'calibration' in kwargs.keys():
            self.use_calibrator=True
            self.flows_according_to_meter=kwargs['calibration'][1]
            self.flows_according_to_mfc=kwargs['calibration'][0]
        else:
            self.use_calibrator=False
        
        """ Constructor for an Aalborg DPC mass flow controller widget."""
        # Initialize the superclass with most of the widget functionality
        super().__init__(parent_dashboard,name,nickname,'#00A36C',default_serial_port=default_serial_port,
                         baudrate=9600,update_every_n_cycles=2)
        # Input fields: select gas, mode, setpoint
        self.gas_options=gas_options
        self.gas_numbers=gas_numbers #Indices in the Aalborg MFC list of gases
        self.add_field(field_type='dropdown',name='Gas Selection',
                       label='Select Gas: ', default_value=default_gas, log=True, options=self.gas_options)
        self.mode_options=['Closed','Setpoint','Open']
        self.add_field(field_type='dropdown',name='Mode Selection',
                       label='Select Mode: ',default_value='Closed', log=True, options=self.mode_options)
        self.add_field(field_type='text input', name='Setpoint Entry', label='Enter Setpoint (sccm): ', default_value='0.0',log=True)
        # Output fields: gas status, mode reading, flow reading. move_field is used to make widget more compact.
        self.add_field(field_type='text output',name='Device Gas',label='Actual: ',default_value='None',log=True,column=2,row=3)
        self.add_field(field_type='text output',name='Device Mode',label='Actual: ',default_value='None',log=True,column=2,row=4)
        self.add_field(field_type='text output',name='Device Setpoint',label='Actual: ',default_value='None',log=True,column=2,row=5)
        self.add_field(field_type='text output',name='Actual Flow',label='Actual Flow (sccm): ',default_value='None',log=True)

    def on_failed_serial_open(self):
        """If serial failed to open, set the readouts to 'no reading'.
        """
        # If handshake failed, set readouts to 'none'
        for f in ('Device Gas','Device Mode','Device Setpoint','Actual Flow'):
            self.set_field(f,'No Reading',hush_warning=True)
                
    def on_handshake(self):
        """Conduct a handshake and populate the default values."""
        # Do a query and a read
        self.on_update()
        # Populate the fields with their default values
        self.set_field('Setpoint Entry',self.get_field('Device Setpoint')) #Set default scale factor to be the device's current scale factor
        self.set_field('Mode Selection',self.get_field('Device Mode')) #Set default mode to be the device's current mode
        if self.get_field('Device Gas') in self.gas_options:
            self.set_field('Gas Selection',self.get_field('Device Gas')) #Set default mode to be the device's current mode

    def on_update(self):
        """Send four queries to the serial device asking for the gas selection, mode, setpoint, and actual flow rate.
        Mode refers to open, closed, or setpoint. Read and process the responses.
        """
        # Do the writes
        s = self.get_serial_object()
        if not self.parent_dashboard.offline_mode:
            s.reset_input_buffer()
        queries = [b'G\r',b'V,M\r',b'SP\r',b'FM\r'] #Gas, mode, setpoint, flow rate)
        for q in queries:
            if (not self.parent_dashboard.offline_mode) and self.parent_dashboard.serial_connected:
                s.write(q)
            time.sleep(0.1)
        # Do the reads
        if not self.parent_dashboard.serial_connected:
            return
        if not self.parent_dashboard.offline_mode:
            lines=self.get_serial_object().readlines()
        else:
            setpoint = 30
            setpoint_str = 'SP:'+str(setpoint)+'\r'
            reading_str = '>'+str(setpoint+np.random.randint(0,5))+'\r'
            lines = (b'G:1,AR\r',b'VM:A\r',setpoint_str.encode('ascii'),reading_str.encode('ascii'))
        # Parse the reads
        try:
            # Parse the Gas data
            gas = lines[0]
            gas = gas[gas.index(b':')+1:]
            gas = gas[gas.index(b',')+1:gas.index(b'\r')]
            self.set_field('Device Gas',gas.decode('ascii'))
            # Parse the Mode data
            mode_status = lines[1]
            mode_start = mode_status.index(b"VM")
            mode_end = mode_status.index(b'\r')
            mode_status = mode_status[mode_start+3:mode_end]
            if mode_status == b'C': # syntax from MFC
                mode_status = "Closed" # syntax for GUI
            if mode_status == b'A':
                mode_status = "Setpoint"
            if mode_status == b'O':
                mode_status = "Open"
            self.set_field('Device Mode',mode_status)
            # Parse the Setpoint data
            setpoint_status = lines[2]
            setpoint_start = setpoint_status.index(b"SP")
            setpoint_end = setpoint_status.index(b"\r")
            setpoint_status = setpoint_status[setpoint_start+3:setpoint_end]
            setpoint_value = max(0,float(setpoint_status))
            if self.use_calibrator:
                setpoint_value = np.interp(setpoint_value,
                                           self.flows_according_to_mfc,self.flows_according_to_meter)# Serial reports a setpoint acc. to the MFC; need to display actual 
            setpoint_str = "{:.1f}".format(setpoint_value)
            self.set_field('Device Setpoint',setpoint_str)
            # Parse the flow data
            flow_status = lines[3]
            flow_start = flow_status.index(b">")
            flow_end = flow_status.index(b"\r")
            flow_status = flow_status[flow_start+1:flow_end]
            flow_value = (max(0,float(flow_status)))
            if self.use_calibrator:
                flow_value = np.interp(flow_value,
                                           self.flows_according_to_mfc,self.flows_according_to_meter)# Serial reports a flow acc. to the MFC; need to display actual 
            flow_str = "{:.1f}".format(flow_value)
            self.set_field('Actual Flow',flow_str)
        except Exception as e:
            for f in ('Device Gas','Device Mode','Device Setpoint','Actual Flow'):
                self.set_field(f,'Read Error',hush_warning=True)
                print("Bad response in Aalborg MFC, in one of: "+str(lines))
        return True
            
    def on_serial_close(self):
        """When serial is closed, set all readouts to 'None'."""
        for f in ('Device Gas','Device Mode','Device Setpoint','Actual Flow'):
            self.set_field(f,'None',hush_warning=True)
            
    def on_confirm(self):
        """When 'confirm' is pressed, send the appropriate commands to the MFC.
        Prints warnings to console if the entered parameters are invalid.
        """
        # Update the MFC gas:
        gas = self.get_field('Gas Selection')
        g = gas
        if not(gas in self.gas_options):
            print("\"Confirm\" pressed with no/invalid gas option selected.")
            return
        gas = str(self.gas_numbers[self.gas_options.index(gas)]).encode('ascii')
        gas_cmd=(b'G,'+gas+b'\r')
        # Update the mode:
        mode=self.get_field('Mode Selection')
        m = mode
        change_sp = (mode=='Setpoint')
        if not(mode in self.mode_options):
            print("\"Confirm\" pressed with no/invalid mode option selected.")
            return
        mode_chars = ("C","A","O")
        mode = str(mode_chars[self.mode_options.index(mode)]).encode('ascii')
        mode_cmd=(b'V,M,'+mode+b'\r')
        # Update the setpoint
        try:
            setpoint = (self.get_field('Setpoint Entry'))
            sp = setpoint
            setpoint = float(setpoint)
            if self.use_calibrator:
                setpoint = np.interp(setpoint,
                                           self.flows_according_to_meter,self.flows_according_to_mfc)# We command a 'real' setpoint; compute what the MFC should measure to achieve that 
            setpoint = '{:.2e}'.format(setpoint)
        except Exception as e:
            print("Enter setpoint number as an int or float.")
            return
        setpoint=setpoint.encode('ascii')
        setpoint_cmd=(b'SP,'+setpoint+b'\r')
        for cmd in [gas_cmd, mode_cmd, setpoint_cmd]:
            if self.parent_dashboard.serial_connected:
                self.serial_object.write(cmd)
                time.sleep(0.1)
        # Print to console
        print("MFC '"+str(self.name)+"' set to gas "+g+", mode "+m+((", setpoint "+sp+" sccm.") if change_sp else '.'))

