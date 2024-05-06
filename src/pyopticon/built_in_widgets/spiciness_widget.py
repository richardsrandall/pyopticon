import numpy as np
import time

# This is a silly demo of how to use the 'no_serial=True' option for devices that don't have a serial connection
# Test the superclass genericWidget
from .. import generic_widget

class SpicinessWidget(generic_widget.GenericWidget):
    """ This is a silly demonstration of extending the GenericWidget class to make a widget that has no serial connection and only updates every few seconds. 
    The superclass constructor is called with no_serial=True and update_every_n_cycles=3. The widget simply reports how spicy it's feeling with a value 
    randomly selected from a list. \n
    
    The use_serial=False option is intended to allow the creation of widgets that 
    do something besides poll a serial connection to update their information, but still have access to the data-logging and other machinery of the GenericWidget class. You might use this to: 

    - Make a widget that communicates with a physical device through some means other than a Pyserial serial connection, e.g. a Python package provided by the instrument vendor.
    - Make a widget that reads the latest values from some instrument's logfile on the computer. This can simplify post-experiment data fusion even if the entire instrument (e.g., a 
      gas chromatograph) is far too complex to configure and run with a PyOpticon interface alone.
    - Make a standalone widget, e.g. a handy calculator, that has GUI elements but doesn't interface with any physical devices.\n

    The update_every_n_cycles option is meant to help interface with instruments that update less than once per second or take a long time to query. For example, a gas chromatograph 
    will only log new concentration data every few minutes, while reading its logfile may be a slow operation, so polling it every 10 or 20 seconds is plenty and avoids gumming up the program with 
    unnecessary reads. Similarly, if a device for some reason required serial queries to be spaced 200ms apart, and one needed to make 6 queries to extract all the data one wanted from 
    it, beginning a sequence of 6 queries every second would overwhelm the instrument. Using update_every_n_cycles to start a sequence of 6 queries every other or every third second would 
    avoid that issue.

    :param parent_dashboard: The dashboard object to which this device will be added
    :type parent_dashboard: pyopticon.dashboard.PyOpticonDashboard
    :param name: The name that the widget will be labeled with, and under which its data will be logged, e.g. "Methane Mass Flow Controller"
    :type name: str
    :param nickname: A shortened nickname that can be used to identify the widget in automation scripts, e.g. "CH4 MFC"
    :type nickname: str
    
    """

    def __init__(self,parent_dashboard,name,nickname):
        """ Constructor for a spiciness widget."""
        # Initialize the superclass with most of the widget functionality
        super().__init__(parent_dashboard,name,nickname,'#FF0000',use_serial=False,update_every_n_cycles=3)
        # Add a readout field
        self.add_field(field_type='text output', name='Spiciness',
                       label='Spiciness: ', default_value='No Reading', log=True)

    def on_failed_serial_open(self,success):
        """Set readout to 'no reading' if initialization failed.
        """
        self.set_field('Spiciness','No Reading')

    def on_update(self):
        """Update the device by polling the serial connection.
        """
        self.on_serial_query()
        time.sleep(0.2)
        if self.parent_dashboard.serial_connected:
            self.on_serial_read()

    def on_serial_query(self):
        """"Nothing is done on a serial query for this device."""
        pass

    def on_serial_read(self):
        """Updates the readout with a randomly selected level of spiciness. Returns True if this process was successful and False otherwise.

        :return: True if the device updated itself successfully, False otherwise.
        :rtype: bool"""
        possible_spiciness = ("Mild","Medium","Hot","Flamin' Hot!!!!")
        spice_index = np.random.randint(0,len(possible_spiciness))
        spice = possible_spiciness[spice_index]
        self.set_field('Spiciness',spice)
        return True

    def on_serial_close(self):
        """When serial is closed, set all readouts to 'None'."""
        self.set_field('Spiciness','No Reading',hush_warning=True)



    
