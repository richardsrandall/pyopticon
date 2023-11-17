from tkinter import *
import tkinter.font as tkFont

class MinimalWidget:
    """Superclass for creating widgets entirely from scratch, without any of the automation or data logging machinery in 
    the GenericWidget class. This is mostly useful for creating widgets that are entirely cosmetic, e.g. the TitleWidget class. 
    This superclass implements all functions required to interact with a Dashboard, but none of them do anything.

    :param parent_dashboard: The dashboard object to which this device will be added
    :type parent_dashboard: pyopticon.dashboard.PyOpticonDashboard
    """

    def __init__(self,parent_dashboard):
        """ Constructor for a minimal widget."""
        self.frame = Frame(parent_dashboard.get_tkinter_object())

    def get_frame(self):
        """ Get the widget's Tkinter frame object."""
        return self.frame

    def show_serial(self):
        """ This method must be implemented in all widgets; in this case, it is empty."""
        pass

    def hide_serial(self):
        """ This method must be implemented in all widgets; in this case, it is empty."""
        pass

    def update_serial_ports(self, new_com_options):
        """ This method must be implemented in all widgets; in this case, it is empty.
        
        :param new_com_options: A list containing the names (strings) of the available serial ports.
        :type new_com_options: list
        """
        pass

    def _call_build_serial_object(self):
        """ This method must be implemented in all widgets; in this case, it is empty."""
        pass

    def open_serial(self):
        """ This method must be implemented in all widgets; in this case, it is empty."""
        pass

    def query_serial(self):
        """ This method must be implemented in all widgets; in this case, it is empty."""
        pass

    def read_serial(self):
        """ This method must be implemented in all widgets; in this case, it is empty."""
        pass

    def close_serial(self):
        """ This method must be implemented in all widgets; in this case, it is empty."""
        pass
