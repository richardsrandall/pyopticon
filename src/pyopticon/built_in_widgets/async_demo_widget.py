import numpy as np
import asyncio
from async_tkinter_loop import async_handler

# This is a silly demo of how to use the 'no_serial=True' option for devices that don't have a serial connection
# Test the superclass genericWidget
from pyopticon import generic_widget

class VibeCheckWidget(generic_widget.GenericWidget):
    """ This is a silly widget meant to demonstrate using Asyncio to update widget fields. A poll_device async function is defined, then executed by the on_serial_query function. 

    :param parent_dashboard: The dashboard object to which this device will be added
    :type parent_dashboard: pyopticon.dashboard.PyOpticonDashboard
    :param name: The name that the widget will be labeled with, and under which its data will be logged, e.g. "Methane Mass Flow Controller"
    :type name: str
    :param nickname: A shortened nickname that can be used to identify the widget in automation scripts, e.g. "CH4 MFC"
    :type nickname: str
    
    """

    def __init__(self,parent_dashboard,name,nickname):
        """ Constructor for a vibe check widget."""
        # Initialize the superclass with most of the widget functionality
        super().__init__(parent_dashboard,name,nickname,'#0000CC',no_serial=True,update_every_n_cycles=3)
        # Add a readout field
        self.add_field(field_type='text output', name='Vibe',
                       label='Vibes: ', default_value='No Reading', log=True)

    def on_serial_open(self,success):
        """If the device initialized successfully, do nothing; if not, set its readout to 'No Reading'

        :param success: Whether serial opened successfully, according to the return from the on_serial_read method.
        :type success: bool"""
        if not success:
            self.set_field('Vibe','No Reading')

    @async_handler
    async def poll_device(self):
        #print("Querying")
        await asyncio.sleep(1.0)
        #print("Got Response")
        possible_vibes = ("Abysmal","OK","Good","🔥")
        vibe_index = np.random.randint(0,len(possible_vibes))
        vibe = possible_vibes[vibe_index]
        self.set_field('Vibe',vibe)
        self.success_flag=True

    def on_serial_query(self):
        """"Nothing is done on a serial query for this device."""
        self.poll_device()
        self.success_flag=False

    def on_serial_read(self):
        """Updates the readout with a randomly selected vibe. Returns True if this process was successful and False otherwise.

        :return: True if the device updated itself successfully, False otherwise.
        :rtype: bool"""
        return self.success_flag
        # Returning this value is useful for the initial handshake, where on_serial_read (in the absence of a separate on_handshake_read function) 
        # should return False if the connection failed.

    def on_serial_close(self):
        """When serial is closed, set all readouts to 'None'."""
        self.set_field('Vibe','No Reading')

    def construct_serial_emulator(self):
        """No serial emulator is needed for this device, since its normal operation doesn't assume any hardware is present. Returns None.
        
        :return: None
        :rtype: NoneType
        """
        return None


    
