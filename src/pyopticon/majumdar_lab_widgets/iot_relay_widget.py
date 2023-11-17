import numpy as np

from .. import generic_widget
from .. import generic_serial_emulator
import time

class IotRelayWidget(generic_widget.GenericWidget):
    """ Widget for using an Arduino to control a Digital Loggers Internet of Things (IoT) Relay, like this: https://www.digital-loggers.com/iot2.html .
    This can be used for on/off control of pretty much any AC-powered device like a light, fan, or pump.\n

    The arduino is expected to control the IoT relay with a digital output pin and to read serial commands using its built-in USB connection. 
    An arduino nano works well; these typically use mini-B USB connections. The arduino ground and digital output pin get connected to the green connector on the side of the IoT relay. 
    Commands to the arduino are broken up by carriage return and newline characters. The arduino should turn on the IoT relay when the command '1' is received 
    and turn it off when the command '0' is received. Additionally, when the command 'Q' for query is received, it should reply with its status ('1' or '0') 
    followed by a newline or carriage return character.\n

    A suitable arduino sketch (program) to control the IoT relay can quickly be written by analogy to this Arduino forum post: https://forum.arduino.cc/t/serial-commands-to-activate-a-digital-output/49036/3
    A working .ino sketch is also available in the majumdar_lab_widgets source code file on this project's Github.
    
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
        """ Constructor for a Digital Loggers IoT relay controller widget."""
        # Initialize the superclass with most of the widget functionality
        super().__init__(parent_dashboard,name,nickname,'#DD88DD',default_serial_port=default_serial_port,baudrate=115200)
        # Add a dropdown field
        self.mode_options=['Off','On']
        self.add_field(field_type='dropdown', name='Status Selection',label='Selected Status: ',
                       default_value=self.mode_options[0], log=True, options=self.mode_options)
        # Add a readout field
        self.add_field(field_type='text output', name='Actual Status',
                       label='Actual Status: ', default_value='No Reading', log=True)
        # Move the confirm button
        self.move_confirm_button(row=3, column=2)

    def on_serial_open(self,success):
        """If serial opened successfully, do nothing; if not, set readout to 'No Reading'

        :param success: Whether serial opened successfully, according to the return from the on_serial_read method.
        :type success: bool or str
        """
        # If handshake failed, set readout to No Reading
        if success is not True:
            self.set_field('Actual Status','No Reading')
    
    def on_serial_query(self):
        """Send a query to the device asking whether it is currently on or off.
        """
        self.send_via_queue(b'Q\n',0)
        self.send_via_queue(b'Q\n',350)
        # There's a weird issue where anytime you launch the program, the first response from the arduino is "" and needs
        # to be ignored... sending the command twice fixes it.

    def on_serial_read(self):
        """Parse the response from the previous serial query and update the display. Return True if valid and an error string if not.

        :return: True if the response was of the expected format, an error message otherwise.
        :rtype: bool or str
        """
        status = (self.serial_object.readline()).decode('ascii')
        self.serial_object.reset_input_buffer()
        status = status.replace("\n","")
        status = status.replace("\r","")
        if status=='1':
            self.set_field('Actual Status','On')
            return True
        elif status=='0':
            self.set_field('Actual Status','Off')
            return True
        else:
            self.set_field('Actual Status','Read Error')
            fail_message=("Unexpected response received from IoT relay arduino: "+str(status))
            return fail_message # An invalid response was read

    def on_serial_close(self):
        """When serial is closed, set all readouts to 'None'."""
        self.set_field('Actual Status','No Reading')

    def on_confirm(self):
        """When 'confirm' is pressed, send the appropriate commands to the arduino.
        """
        selected = self.get_field('Status Selection')
        if selected=='On':
            self.send_via_queue(b'1\n',50)
            print("Turning on IoT relay: '"+self.nickname+"'")
        elif selected=='Off':
            self.send_via_queue(b'0\n',50)
            print("Turning off IoT relay: '"+self.nickname+"'")

    def construct_serial_emulator(self):
        """Get the serial emulator to use when we're testing in offline mode.

        :return: An IoT relay serial emulator object.
        :rtype: pyopticon.majumdar_lab_widgets.iot_relay_widget.IoTRelaySerialEmulator"""
        return IoTRelaySerialEmulator()

class IoTRelaySerialEmulator(generic_serial_emulator.GenericSerialEmulator):
    """Serial emulator to allow offline testing of dashboards containing IoT relay widgets.
    Acts as a Pyserial Serial object for the purposes of the program, implementing a few of the same methods.
    Confirms to console when an on/off command is sent, and otherwise returns a randomly selected 'on' or 'off' status.
    """
    # This class simulates what a real instrument would respond so I can test code on my laptop
    def write(self,value):
        """Write to this object as if it were a Pyserial Serial object. Ignores queries and reports on/off commands to console."""
        if 'Q' in str(value):#Ignore queries
            return
        print("UV LED got command: "+str(value)+"; ignoring.")

    def readline(self):
        """Reads a response as if this were a Pyserial Serial object. The only time readline is called is to check the response to a status query."""
        v = np.random.randint(0,20)
        v = '1' if v>10 else '0'
        v = str(v)+'\r\n'
        return v.encode('ascii')

