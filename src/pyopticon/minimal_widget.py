from tkinter import *
import tkinter.font as tkFont
import time
import queue

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
        self.queue = queue.Queue()
        self.doing_update=False
        self.shutdown_flag = False

    def on_handshake(self):
        """Runs when serial is connected. Does nothing unless overridden."""
        pass

    def on_update(self):
        """Runs every update cycle. Does nothing unless overridden."""
        pass

    def on_serial_close(self):
        """Runs on serial close. Does nothing unless overridden."""
        pass

    def on_confirm(self):
        """Runs on 'confirm', though these widgets generally don't have confirm buttons unless you add one. Does nothing unless overridden."""
        pass

    # Widgets to run the thread

    def _run_thread(self):
        """Launch a thread to process commands from the widget's queue."""

        while True:
            if self.shutdown_flag:
                return
            try:
                while not self.queue.empty():
                    (cmd,widget) = self.queue.get()
                    
                    if cmd == 'UPDATE': # Update the widget however desired
                        self.doing_update = True
                        widget.on_update()
                        self.doing_update = False # Flag to let us warn if the polling interval is too short

                    elif cmd == 'CONFIRM': # Tell the thread to update the system state
                        widget.on_confirm()

                    elif cmd == 'HANDSHAKE': # Tell the thread to open serial and do the handshake
                        widget.on_handshake()

            except Exception as e:
                self.parent_dashboard.exc_handler(e,'system',self.name)

            time.sleep(0.05)

    def _shutdown_thread(self):
        """Shutdown the widget's thread once the GUI is closed."""
        self.shutdown_flag = True

    # All widgets must have the below methods; they don't really do anything.

    def close_serial(self):
        self.on_serial_close()

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
