import numpy as np
import time

# Test the superclass genericWidget
from .. import generic_widget
from collections import defaultdict

class MksMFCWidget(generic_widget.GenericWidget):
    """ Widget to control MKS 'mass flo controllers' (MFCs), which are themselves controlled by an MKS 'vacuum controller'.\n

    A control box like an MKS '946 Vacuum System Controller' converts digital signals or manual inputs into the actual voltage and/or current 
    signals that control MKS mass flo controllers. One 946 control box can control up to 6 mass flo controllers at once, with some trickery required (described below) to let multiple widgets share a single serial connection.\n

    Each control box has a 3-digit ID number, e.g. 001, which can be configured on the box. Each MFC on the box has a channel, which is one of {A1, A2, B1, B2, C1, C2}. These are fixed when you initialize a widget and can't be changed from the GUI.\n

    Each mass flo controller on the same vacuum controller gets its own widget, even though they all share the same control box and hence the same serial connection.
    The first MFC widget is initialized normally, and then for every subsequent widget representing an MFC on the same control box, the constructor is called with 
    the first widget passed as the keyword argument 'widget_to_share_serial_with'. The later widgets then know to share the serial connection with the first widget, 
    rather than trying to initialize a new one, which would fail because that serial port is already in use by the first widget.\n

    One can also set a 'scale factor,' which adjusts for different gas types (e.g. air is usually a conversion factor of 1.0). Refer to the MKS MFC documentation 
    for what scale factor to use for a particular gas. One can optionally lock the scale factor for a certain widget.

    Finally, one can add a manual calibration curve independent of the scale factor. This is done by tabulating the commanded flow (i.e., the value sent to 
    the MFC) and the actual flow (according to an external flow meter) at various flow conditions, then feeding the resulting tuples of 
    flows to the constructor for this class.
    
    :param parent_dashboard: The dashboard object to which this device will be added
    :type parent_dashboard: richardview.dashboard.RichardViewDashboard
    :param name: The name that the widget will be labeled with, and under which its data will be logged, e.g. "Methane Mass Flow Controller"
    :type name: str
    :param nickname: A shortened nickname that can be used to identify the widget in automation scripts, e.g. "CH4 MFC"
    :type nickname: str
    :param channel: A string representing which channel on the control box the MFC is connected to. One of (A1,A2,B1,B2,C1,C2).
    :type channel: str
    :param widget_to_share_serial_with: If this is the 2nd-6th MFC sharing the same control box, pass the widget for the first MFC on that control box as this argument. If not, the arguments device_ID and default_serial_port are required.
    :type widget_to_share_serial_with: richardview.majumdar_lab_widgets.mks_mfc_widget.MksMFCWidget, optional
    :param device_ID: The ID of the MKS control box / vacuum system controller, which is a string of a 3-digit number, e.g. '001'. Can be set on the control box.
    :type device_ID: str, optional
    :param default_serial_port: The name of the default selected serial port, e.g. 'COM9'
    :type default_serial_port: str, optional
    :param force_scale_factor: Optionally set a certain scale factor and disable adjusting the scale factor via the interface. See the MKS manual to select factors for different gases.
    :type force_scale_factor: float, optional
    :param calibration: a tuple containing two tuples of ints or floats with the results of calibrating the MFC. The first should contain a range of flow commands sent to the MFC. The second should contain the result flows according to an external flow meter. (0,0) should be included, as should a value above the highest flow you expect to use. For example, ( (0,10,20,30), (0,11.5,20.7,33.4) ).
    :type calibration: tuple, optional
    """

    def __init__(self,parent_dashboard,name,nickname,channel,**kwargs):
        """ Constructor for an MKS mass flow controller widget."""

        # Check whether required parameters are present
        if not 'widget_to_share_serial_with' in kwargs.keys():
            if not 'default_serial_port' in kwargs.keys():
                raise Exception("Missing argument initializing MKS MFC -- if widget_to_share_serial_with is not specified, you must specify default_serial_port .")
            if not 'device_id' in kwargs.keys():
                raise Exception("Missing argument initializing MKS MFC -- if widget_to_share_serial_with is not specified, you must specify device_id .")

        # Unpack kwargs
        default_serial_port = kwargs['default_serial_port'] if ('default_serial_port' in kwargs.keys()) else 'None'
        widget_to_share_serial_with = kwargs['widget_to_share_serial_with'] if ('widget_to_share_serial_with' in kwargs.keys()) else None
        self.widget_to_share_serial_with = widget_to_share_serial_with
        self.force_scale_factor = str(kwargs['force_scale_factor']) if ('force_scale_factor' in kwargs.keys()) else ""
        device_id = kwargs['device_id'] if ('device_id' in kwargs.keys()) else widget_to_share_serial_with.device_id
        if 'calibration' in kwargs.keys():
            self.use_calibrator=True
            self.flows_according_to_meter=kwargs['calibration'][1]
            self.flows_according_to_mfc=kwargs['calibration'][0]
        else:
            self.use_calibrator=False

        # Initialize the superclass with most of the widget functionality
        super().__init__(parent_dashboard,name,nickname,'#90ee90',default_serial_port=default_serial_port,baudrate=9600,widget_to_share_thread_with=widget_to_share_serial_with)
        # Store key info about the device
        channel_options = ["A1","A2","B1","B2","C1","C2"]
        self.which_channel = str(channel_options.index(channel)+1)
        self.device_id = device_id
        # Input fields: select gas, mode, setpoint, scale factor
        self.add_field(field_type='text input',name='Scale Factor Entry',
                       label='Enter Scale Factor: ', default_value=self.force_scale_factor, log=True)
        if self.force_scale_factor!="":
            self.disable_field('Scale Factor Entry')
        self.mode_options=['Closed','Setpoint','Open']
        self.add_field(field_type='dropdown',name='Mode Selection',
                       label='Select Mode: ',default_value='Closed', log=True, options=self.mode_options)
        self.add_field(field_type='text input', name='Setpoint Entry', label='Enter Setpoint (sccm): ', default_value='0.0',log=True)
        # Output fields: gas status, mode reading, flow reading. move_field is used to make widget more compact.
        self.add_field(field_type='text output',name='Device Scale Factor',label='Actual: ',default_value='None',log=True,column=2,row=3)
        self.add_field(field_type='text output',name='Device Mode',label='Actual: ',default_value='None',log=True,column=2,row=4)
        self.add_field(field_type='text output',name='Device Setpoint',label='Actual: ',default_value='None',log=True,column=2,row=5)
        self.add_field(field_type='text output',name='Actual Flow',label='Actual Flow (sccm): ',default_value='None',log=True)
        # Move the confirm buttom
        self.move_confirm_button(row=6,column=3)

    def on_failed_serial_open(self):
        """If serial opened unsuccessfully, set readouts to 'No Reading'
        """
        for f in ('Device Scale Factor','Device Mode','Device Setpoint','Actual Flow'):
            self.set_field(f,'No Reading',hush_warning=True)

    def on_handshake(self):

        # Do an update
        self.on_update()

        # Populate the default field values
        if self.force_scale_factor=="":
            self.set_field('Scale Factor Entry',self.get_field('Device Scale Factor')) #Set default scale factor to be the device's current scale factor
        self.set_field('Setpoint Entry',self.get_field('Device Setpoint')) #Set default scale factor to be the device's current scale factor
        self.set_field('Mode Selection',self.get_field('Device Mode')) #Set default mode to be the device's current mode



    def on_update(self):
        """Send four queries to the serial device asking for the gas scale factor, mode, setpoint, and actual flow rate.
        Mode refers to open, closed, or setpoint. Process the results.
        """

        # Reset the input buffer if needed
        s = self.get_serial_object()
        if self.widget_to_share_serial_with is None:
            if not self.parent_dashboard.offline_mode:
                s.reset_input_buffer()

        time.sleep(0.05)
        # Queries serial for all the desired values
        queries = ("QSF","QMD","QSP","FR") #Gas, mode, setpoint, flow rate)
        for query in queries:
            write_me = "@"+str(self.device_id)+query+str(self.which_channel)+"?;FF\r"
            write_me = write_me.encode('ascii')
            if not self.parent_dashboard.offline_mode:
                s.write(write_me)
                time.sleep(0.05)

        # Wait and bail if needed        
        time.sleep(0.5)
        if not self.parent_dashboard.serial_connected:
            return
        

        # We need to manually read the next 4 replies, since the commands are delimited by ;, not \r or \n
        try:
            if not self.parent_dashboard.offline_mode:
                raw_lines=[]
                for i in range(4):
                    line=""
                    for j in range(20):
                        onebyte = self.get_serial_object().read(1)
                        if onebyte==b';':
                            raw_lines.append(str(line))
                            line=""
                            break
                        else:
                            line += str(onebyte.decode("ascii"))
                lines = list(raw_lines)
            else:
                reading_str = '@001ACK'+str(round(8.01+0.1*np.random.randint(0,5),2))+'e+1;FF'
                responses = ['@253ACK3.40E-01', 'FF@253ACKCLOSE', 'FF@253ACK1.00E+02', reading_str]
                lines = list(responses)
        except Exception as e:
            for f in ('Device Scale Factor','Device Mode','Device Setpoint','Actual Flow'):
                self.set_field(f,'Read Error')
            fail_message=("Failed to read from MKS MFC; likely an MFC that this shares a serial line with failed to connect.")
            #print(fail_message)
        try:
            # Parse the scale factor data
            lines = [str(l) for l in lines]
            scale_factor = lines.pop(0).replace('FF','')
            scale_factor = scale_factor[scale_factor.index("ACK")+3:]
            scale_factor = max(0,float(scale_factor))
            scale_factor = "{:.1f}".format(scale_factor)
            self.set_field('Device Scale Factor',scale_factor)
            # Parse the Mode data
            mode_status = lines.pop(0).replace('FF','')
            mode_status = mode_status[mode_status.index("ACK")+3:]
            if mode_status == "CLOSE":
                mode_status = "Closed"
            if mode_status == "OPEN":
                mode_status = "Open"
            if mode_status == "SETPOINT":
                mode_status = "Setpoint"
            self.set_field('Device Mode',mode_status)
            # Parse the Setpoint data
            setpoint_status = lines.pop(0).replace('FF','')
            setpoint_status = setpoint_status[setpoint_status.index("ACK")+3:]
            setpoint_value = max(0,float(setpoint_status))
            if self.use_calibrator:
                setpoint_value = np.interp(setpoint_value,
                                           self.flows_according_to_mfc,self.flows_according_to_meter)# Serial reports a setpoint acc. to the MFC; need to display actual 
            setpoint_status = "{:.1f}".format(setpoint_value)
            self.set_field('Device Setpoint',setpoint_status)
            # Parse the flow data
            flow_status = lines.pop(0).replace('FF','').replace(";","")
            flow_status = flow_status[flow_status.index("ACK")+3:]
            flow_status = flow_status.replace(">","")
            flow_value = max(0,float(flow_status))
            if self.use_calibrator:
                flow_value = np.interp(flow_value,
                                           self.flows_according_to_mfc,self.flows_according_to_meter)# Serial reports a flow acc. to the MFC; need to display actual 
            flow_status = "{:.1f}".format(flow_value)
            self.set_field('Actual Flow',flow_status)
        except Exception as e:
            for f in ('Device Scale Factor','Device Mode','Device Setpoint','Actual Flow'):
                self.set_field(f,'Read Error')
            fail_message=("Bad response in MKS MFC, in one of: "+str(lines))
            
    def on_serial_close(self):
        """When serial is closed, set all readouts to 'None'."""
        for f in ('Device Scale Factor','Device Mode','Device Setpoint','Actual Flow'):
            self.set_field(f,'None',hush_warning=True)

    def on_confirm(self):
        """When 'confirm' is pressed, send the appropriate commands to the MFC.
        Prints warnings to console if the entered parameters are invalid.
        """
        s = self.get_serial_object()
        # Update the scale factor:
        sf = self.get_field('Scale Factor Entry')
        try:
            sf = float(sf)
            sf = '{0:.2f}'.format(sf)
            sf_command = ("@"+self.device_id+"QSF"+self.which_channel+"!"+sf+";FF\r").encode('ascii')
            time.sleep(0.1)
            if (self.parent_dashboard.serial_connected) and (not self.parent_dashboard.offline_mode):
                self.serial_object.write(sf_command)
        except Exception as e:
            print("Enter scale factor as an int or float.")
            return
        # Update the mode:
        mode=self.get_field('Mode Selection')
        m = mode
        change_sp = True#(mode=='Setpoint') #Better to always change the setpoint
        if not(mode in self.mode_options):
            print("\"Confirm\" pressed with no/invalid mode option selected.")
            return
        send_values = ["CLOSE","SETPOINT","OPEN"]
        mode_selected = send_values[self.mode_options.index(mode)]
        mode_command = ("@"+self.device_id+"QMD"+self.which_channel+"!"+mode_selected+";FF\r").encode('ascii')
        time.sleep(0.1)
        if (self.parent_dashboard.serial_connected) and (not self.parent_dashboard.offline_mode):
            self.serial_object.write(mode_command)
        # Update the setpoint if needed:
        if change_sp:
            try:
                setpoint = (self.get_field('Setpoint Entry'))
                sp = setpoint
                setpoint = float(setpoint)
                if self.use_calibrator:
                    setpoint = np.interp(setpoint,
                                         self.flows_according_to_meter,self.flows_according_to_mfc)# We command a 'real' setpoint; compute what the MFC should measure to achieve that 
                setpoint = '{:.2e}'.format(setpoint)
                setpoint_command = ("@"+self.device_id+"QSP"+self.which_channel+"!"+setpoint+";FF\r").encode('ascii')
                time.sleep(0.1)
                if (self.parent_dashboard.serial_connected) and (not self.parent_dashboard.offline_mode):
                    self.serial_object.write(setpoint_command)
            except Exception as e:
                print("Enter setpoint number as an int or float.")
                return
        # Print to console
        print("MFC '"+str(self.name)+"' set to scale factor "+sf+", mode "+m+((", setpoint "+sp+" sccm.") if change_sp else '.'))
        




