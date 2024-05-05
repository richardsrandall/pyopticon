import numpy as np
import time
import traceback

# Test the superclass genericWidget
from .. import generic_widget

class OmegaUSBUTCWidget(generic_widget.GenericWidget):
    """ Widget for an Omega USB-UTC thermocouple reader. 
    A USB-UTC converts a single thermocouple (using the usual 2-prong thermocouple connection) into a USB signal. The Omega thermocouple reader desktop app can be 
    used to set what type of thermocouple (K-type, etc.) is assumed.

    :param parent_dashboard: The dashboard object to which this device will be added
    :type parent_dashboard: pyopticon.dashboard.PyOpticonDashboard
    :param name: The name that the widget will be labeled with, and under which its data will be logged, e.g. "Methane Mass Flow Controller"
    :type name: str
    :param nickname: A shortened nickname that can be used to identify the widget in automation scripts, e.g. "CH4 MFC"
    :type nickname: str
    :param default_serial_port: The name of the default selected serial port, e.g. 'COM9'
    :type default_serial_port: str
    """

    def __init__(self,parent_dashboard,name,nickname,default_serial_port):
        """ Constructor for an Omega USB-UTC thermocouple widget."""
        # Initialize the superclass with most of the widget functionality
        super().__init__(parent_dashboard,name,nickname,'#CBC3E3',default_serial_port=default_serial_port,baudrate=38400)
        # Add a readout field
        self.add_field(field_type='text output', name='Temperature',
                       label='Temperature (C): ', default_value='No Reading', log=True)

    def on_failed_serial_open(self):
        """If serial opened successfully, do nothing; if not, set readouts to 'No Reading'
        """
        # If handshake failed, set readout to 'none'
        self.set_field('Temperature','No Reading',hush_warning=True)

    def on_update(self):
        """Update the device by polling the serial connection.
        """
        self.on_serial_query()
        time.sleep(0.5)
        if not self.parent_dashboard.serial_connected:
            return
        self.on_serial_read()


    def on_serial_query(self):
        """Send a query to the serial device asking for the temperature.
        """
        if not self.parent_dashboard.offline_mode:
            self.get_serial_object().write(b'C\r')

    def on_serial_read(self):
        """Parse the responses from the previous serial query and update the display. Return True if valid and and error string if not.

        :return: True if the response was of the expected format, an error string otherwise.
        :rtype: bool or str
        """
        try:
            if not self.parent_dashboard.offline_mode:
                status = self.get_serial_object().readline()
                self.get_serial_object().reset_input_buffer()
            else:
                status = ("b'>"+str(30+np.random.randint(0,5))+"\r\n'")
            status = str(status)
            if len(status)<6 or len(status)>11: #Should receive something like b'>25\r\n'
                raise Exception('Invalid Response Read')
            num_filter = filter(str.isdigit, status)
            status = "".join(num_filter)
            if self.parent_dashboard.serial_connected:
                self.set_field('Temperature',status)
            if len(status)==0:
                raise Exception('Invalid Response Read')
            return True # A valid response from the TC was read
        except Exception as e:
            print("'"+str(status)+"'")
            self.set_field('Temperature','Read Error')

    def on_serial_close(self):
        """When serial is closed, set all readouts to 'None'."""
        self.set_field('Temperature','No Reading',hush_warning=True)

