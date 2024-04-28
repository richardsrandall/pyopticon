from tkinter import *
import serial.tools.list_ports
import platform
import traceback

# Serial widget
class SerialWidget:
    
    """ This widget is responsible for prompting all of the widgets to open serial connections, query them regularly, 
    check them for responses, and closing the connections when needed. It also has the button to update the list of serial ports.

    :param parent: The dashboard to which this widget will be added.
    :type parent: pyopticon.dashboard.Dashboard
    """

    def __init__(self, parent_dashboard, polling_interval):
        """The constructor for the SerialWidget"""
        # Parent is the labGUI object, root is the tkinter root object
        # Set polling interval
        self.parent = parent_dashboard
        self.root = parent_dashboard.get_tkinter_object()
        self.serial_polling_wait = polling_interval # Poll serial ports every X milliseconds
        self.main_color = '#FF7F7F'
        # Widget for all serial connections
        self.frame = Frame(self.root,highlightbackground=self.main_color, highlightcolor=self.main_color, highlightthickness=5)
        self.control_label = Label(self.frame,text="Control Serial Communication")
        self.control_label.grid(row=1,column=1,sticky='nesw')
        # Open/close serial communication logic
        self.connect_serial_text = StringVar()
        self.connect_serial_text.set("Start polling devices")
        self.parent.serial_connected = False
        Button(self.frame,textvariable=self.connect_serial_text,command = self._toggle_serial_connected).grid(row=2,column=1,sticky='nesw')
        # Serial port updating logic
        self.update_ports_button = Button(self.frame,text="Update Serial Ports",command=self._update_serial_ports)
        self.update_ports_button.grid(row=3,column=1,sticky='nesw')

    def get_frame(self):
        """Get the tkinter frame on which this object is drawn.
        
        :return: The widget's tkinter frame
        :rtype: tkinter.Frame
        """
        return self.frame

    # Methods to support serial communication and show/hide functionality            
    def _toggle_serial_connected(self):
        """Toggle whether serial communications are active. Prompt all widgets to open or close serial connections. 
        Grey out and change text on the appropriate GUI buttons while serial communications are active."""
        if self.parent.serial_connected:
            # Close the serial connections
            self.connect_serial_text.set("Start polling devices")
            self.parent.serial_connected = False
            self.update_ports_button.configure(state='normal')
            for obj in self.parent.all_widgets:
                obj.close_serial()
            print("All connections closed.")
        else:
            # Open the serial connections
            self.connect_serial_text.set("Stop polling devices")
            self.parent.serial_connected = True
            self.update_ports_button.configure(state='disabled')#So you can't update serials while serial is polling
            for obj in self.parent.all_widgets:
                try:
                    obj._call_build_serial_object() # Opens the serial object for each widget
                except Exception:
                    print(traceback.format_exc())#Print a full error report
            for obj in self.parent.all_widgets:
                try:
                    obj.open_serial()
                    # In each object, open_serial first queries, then waits as long as is necessary, then reads, 
                    # then calls on_serial_open. This is done by means of separate tkinter after() calls in each widget.
                except Exception as e:
                    print(traceback.format_exc())#Print a full error report
            # Some widgets may require more than one cycle to complete their handshake, so we figure out which widget 
            # requires the longest handshake time, and make the handshake period last that long.
            max_interval = 1
            for obj in self.parent.all_widgets:
                if hasattr(obj,'update_every_n_cycles'):
                    if obj.update_every_n_cycles>max_interval:
                        max_interval=obj.update_every_n_cycles
            # After the handshake period is done, we start polling serial ports as normal.
            self.root.after(self.serial_polling_wait*max_interval,lambda: self._poll_serial_ports())
            self.root.after(self.serial_polling_wait*max_interval-50,lambda: print("All connections opened."))

    def _poll_serial_ports(self):
        """So long as serial communications are active, poll all widgets by calling this widget's own methods that prompt all widgets to query and read. Also, execute all interlock functions in the interlock list."""
        self._query_serial_ports()
        self.root.after(int(self.serial_polling_wait*0.5), self._read_serial_ports)
        if self.parent.serial_connected:
            self.root.after(self.serial_polling_wait,self._poll_serial_ports)
            self._poll_interlocks()
            
    def _query_serial_ports(self):
        """Prompt every widget to send a query through its serial port, asking its physical device for a status update. Check for unrecoverable serial errors that occasionally result from defective RS232 converters and splitters."""
        if not self.parent.serial_connected:
            return
        for obj in self.parent.all_widgets:
            try:
                obj.query_serial()
                obj.failure_flag = False
            except Exception as e:
                if hasattr(obj,'failure_flag'):
                    if not obj.failure_flag:
                        print("Serial error in "+obj.name+". No further readings possible.")
                obj.failure_flag = True
                try:
                    obj.close_serial()#Change GUI to reflect that it disconnected
                    obj.serial_status.set("Failed to Query.")
                except Exception as e:
                    pass
                

    def _read_serial_ports(self):
        """Prompt every widget to read the lastest responses from its serial port and update its display accordingly."""
        if not self.parent.serial_connected:
            return
        for obj in self.parent.all_widgets:
            try:
                obj.read_serial()
            except Exception as e:
                pass

    def _poll_interlocks(self):
        """Execute every interlock function that has been added to the dashboard."""
        for fn in self.parent.all_interlocks:
            try:
                fn()
            except Exception as e:
                print("Running interlock test failed:")
                print(e)

    def _update_serial_ports(self):
        """Update the drop-down menu of available serial ports, accounting for any ports that have appeared/disappeared since this method was last called."""
        if self.parent.serial_connected:
            print("Can't update serial ports while serial is connected.")
            return
        ports = serial.tools.list_ports.comports()
        if len(ports)==0:
            new_serials = ["[No Serial Ports Found]"]
        elif 'COM' in ports[0].name:
            com_numbers = []
            for port in ports:
                com_numbers.append(int(port.name.replace("COM","")))
            com_numbers.sort()
            new_serials = []
            for num in com_numbers:
                new_serials.append("COM"+str(num))
        else:
            ports.sort()
            new_serials = ports
        for obj in self.parent.all_widgets:
            obj.update_serial_ports(new_serials)
    
