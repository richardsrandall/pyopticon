import numpy as np
import time

from .. import generic_widget

class Valco2WayValveWidget(generic_widget.GenericWidget):
    """ Widget for a VICI Valco 2-position valve, like this: https://www.vici.com/vval/vval_2pos.php . 
    These valves have two positions that are internally referred to as 'A' and 'B'. In the widget, the positions can be labeled whatever you want.\n

    Valco produces many other valves, e.g. 9-way selector valves. To control one of them, you could probably copy-paste the source code of this module and make pretty minor modifications 
    to on_serial_query, on_serial_read, on_confirm, and the serial emulator class. Refer to the valve's documentation and/or mess around manually with a serial connection 
    (Pyserial in a shell like IDLE is probably easiest) to figure out the serial protocol for controlling a different type of Valco valve -- e.g., valves with more than 2 positions may 
    label the positions with numbers rather than letters in the serial protocol.
    
    :param parent_dashboard: The dashboard object to which this device will be added
    :type parent_dashboard: pyopticon.dashboard.PyOpticonDashboard
    :param name: The name that the widget will be labeled with, and under which its data will be logged, e.g. "Methane Mass Flow Controller"
    :type name: str
    :param nickname: A shortened nickname that can be used to identify the widget in automation scripts, e.g. "CH4 MFC"
    :type nickname: str
    :param default_serial_port: The name of the default selected serial port, e.g. 'COM9'
    :type default_serial_port: str
    :param valve_positions: A list of strings with which to label the valve positions. For a 2-way valve, this should be a 2-element list with the labels for valve positions A and B respectively.
    :type valve_positions: list
    :param valve_id: A string representing the ID of the valve, which goes at the beginning of each command. This seems to always be '1'. However, if there are issues, going into a serial shell 
    (e.g. Pyserial in IDLE) and sending the message b'*ID\\r' to the valve should cause it to respond with its ID.
    
    
    """

    def __init__(self,parent_dashboard,name,nickname,default_serial_port,valve_positions,valve_id='1'):
        """ Constructor for a VICI Valco 2-way valve widget."""
        # Initialize the superclass with most of the widget functionality
        super().__init__(parent_dashboard,name,nickname,'#ADD8E6',default_serial_port=default_serial_port,baudrate=9600)
        # Record the valve id
        self.valve_id=valve_id.encode('ascii')
        # Add a dropdown field
        self.valve_positions=valve_positions
        self.add_field(field_type='dropdown', name='Position Selection',label='Selected Position: ',
                       default_value=self.valve_positions[0], log=True, options=self.valve_positions)
        # Add a readout field
        self.add_field(field_type='text output', name='Actual Position',
                       label='Actual Position: ', default_value='No Reading', log=True)
        # Move the confirm button
        self.move_confirm_button(row=3,column=2)

    def on_failed_serial_open(self,success):
        """Set fields to no reading if serial failed to open.
        """
        self.set_field('Actual Position','No Reading',hush_warning=True)

    def on_update(self):
        """Update the widget by querying and reading the serial port.
        """
        self.on_serial_query()
        time.sleep(0.2)
        if self.parent_dashboard.serial_connected:
            self.on_serial_read()

    def on_serial_query(self):
        """Send a query to the valve asking for its current position.
        """
        if not self.parent_dashboard.offline_mode:
            self.get_serial_object().reset_input_buffer()
            to_write=self.valve_id+b'CP\r'
            self.get_serial_object().write(to_write)

    def on_serial_read(self):
        """Parse the responses from the previous serial query and update the display. Return True if the response is valid and an error string if not.
        """
        if not self.parent_dashboard.offline_mode:
            status = str(self.serial_object.readline())
        else:
            v = np.random.randint(0,20)
            v = 'A' if v>10 else 'B'
            v = 'dd"'+str(v)+'dd\r\n'
            status = str(v.encode('ascii'))
        try:
            i = status.index("\"")+1
            is_A = status[i]=='A'
            if is_A:
                self.set_field('Actual Position',self.valve_positions[0])
            else:
                self.set_field('Actual Position',self.valve_positions[1])
        except Exception as e:
            fail_message=("Unexpected response received from 2-way valve: "+str(status))
            if self.parent_dashboard.serial_connected:
                self.set_field('Actual Position','Read Error')

    def on_serial_close(self):
        """When serial is closed, set all readouts to 'None'."""
        self.set_field('Actual Position','No Reading',hush_warning=True)

    def on_confirm(self):
        """When 'confirm' is pressed, send the appropriate commands to the valve.
        """
        selected = self.get_field('Position Selection')
        if not (selected in self.valve_positions):
            print("\"Confirm\" pressed with no/invalid option selected.")
            return
        choice = self.valve_positions.index(selected)
        if choice==0:
            print("Moving valve \""+self.name+"\" to \""+selected+"\" (A)")
            if not self.parent_dashboard.offline_mode:
                self.serial_object.write(self.valve_id+b'GOA\r')
        else:
            print("Moving valve \""+self.name+"\" to \""+selected+"\" (B)")
            if not self.parent_dashboard.offline_mode:
                self.serial_object.write(self.valve_id+b'GOB\r')


    
