from tkinter import *
import ctypes
import serial
import time
import traceback

class GenericWidget:
    """This is the superclass for all widgets representing physical devices. It contains a lot of the machinery for 
    generating GUI elements, setting up a serial connection, and logging data, so that subclass implementation is mostly defining the 
    input/output fields and the serial communication protocol for a given instrument.
    
    :param parent_dashboard: The dashboard object to which this device will be added
    :type parent_dashboard: pyopticon.dashboard.PyOpticonDashboard
    :param name: The name that the widget will be labeled with, and under which its data will be logged, e.g. "Methane Mass Flow Controller"
    :type name: str
    :param nickname: A shortened nickname that can be used to identify the widget in automation scripts, e.g. "CH4 MFC"
    :type nickname: str
    :param default_serial_port: The name of the default selected serial port, e.g. 'COM9'
    :type default_serial_port: str
    :param color: The color of the widget's frame, as a RGB hex string, e.g. '#00FF00'
    :type color: str
    :param no_serial: True if this widget does not need to have a serial connection; False otherwise. Defaults to False.
    :type no_serial: bool, optional
    :param default_serial_port: The name of the default selected serial port, e.g. 'COM9'. Required unless no_serial is True.
    :type default_serial_port: str, optional
    :param baudrate: The baud rate of the serial connection, as an integer, e.g. 19200. Required unless no_serial is True or build_serial_object is overridden.
    :type baudrate: int, optional
    :param widget_to_share_serial_with: A widget whose Pyserial Serial object this widget will share, rather than creating its own. Useful if multiple widgets need to share the same serial port. Defaults to None.
    :type widget_to_share_serial_with: pyopticon.generic_widget.GenericWidget, optional
    :param update_every_n_cycles: Set the widget to poll its serial connection for updates every n cycles. Useful for instruments that poll slowly for some reason, or whose state changes infrequently. Defaults to 1.
    :type update_every_n_cycleS: int, optional
    """

    def __init__(self,parent_dashboard,name,nickname,color,**kwargs):
        """Constructor for a GenericWidget"""

        # Unpack basic arguments
        self.name = name
        self.nickname = nickname
        self.serial_object = None

        # Unpack kwargs
        no_serial = kwargs['no_serial'] if ('no_serial' in kwargs.keys()) else False
        self.default_serial = kwargs['default_serial_port'] if not no_serial else None
        self.baudrate = kwargs['baudrate'] if ('baudrate' in kwargs.keys()) else None
        update_every_n_cycles = kwargs['update_every_n_cycles'] if ('update_every_n_cycles' in kwargs.keys()) else 1
        widget_to_share_serial_with = kwargs['widget_to_share_serial_with'] if ('widget_to_share_serial_with' in kwargs.keys()) else None

        self.serial_shared = (widget_to_share_serial_with!=None) # Share the serial connection with a previously constructed device
        self.widget_to_share_serial_with=widget_to_share_serial_with
        self.serial_emulator = None
        self.no_serial = no_serial
        self.update_every_n_cycles=update_every_n_cycles
        self._update_cycle_counter=-1

        # Create a frame, set its style
        self.color = color
        self.frame = Frame(parent_dashboard.get_tkinter_object(), highlightbackground=self.color, highlightcolor=self.color, highlightthickness=5)
        self.parent_dashboard = parent_dashboard
        
        # Create the title
        Label(self.frame,text=name).grid(row=0,column=1)
        
        if not no_serial:
            # Labels associated with serial communications
            if not self.serial_shared:
                self.serial_menu_label = Label(self.frame,text="Select Serial Port: ")
            else:
                self.serial_menu_label = Label(self.frame,text="Serial Shared With: ")
            self.serial_menu_label.grid(row=1,column=0)
            self.serial_readout_label = Label(self.frame,text="Connection status: ")
            self.serial_readout_label.grid(row=2,column=0)
            # Declare the variables that run the serial port
            self.serial_options = ["COM1"]
            self.serial_selected = StringVar() # Serial port selected
            self.serial_selected.set(self.default_serial)
            self.serial_status = StringVar() # Status of serial connection
            self.serial_status.set("Not connected.")
        
            # Add and locate all of the functional serial widgets
            if not self.serial_shared:
                self.serial_menu = OptionMenu(self.frame, self.serial_selected, *self.serial_options)
            else:
                self.serial_menu = Label(self.frame,text=str(self.widget_to_share_serial_with.nickname))
            self.serial_menu.grid(row=1,column=1,sticky='nesw')
            self.serial_readout = Label(self.frame,textvariable=self.serial_status)
            self.serial_readout.grid(row=2,column=1,sticky='nesw')

        # Construct a map of attributes for automation
        self.attributes = dict()
        self.values_to_log = dict()
        self.default_values = dict()
        self.field_gui_objects = dict()
        self.confirm_button_added = False

# Generic methods that can be defined by the user

    def log_data(self):
        """Generate a dict of data that is sent to the dashboard's data logging script. The dict contains the current values of 
        all fields that were created using add_field with the option log=True. This method may be overridden in a subclass if you 
        would like to do some kind of preprocessing on data before it's logged, e.g. stripping out units or typecasting to int or float.
        
        :return: A dict of the widget's loggable fields and their current values
        :rtype: dict"""
        out = dict()
        for k in self.values_to_log.keys():
            out[k]=self.values_to_log[k].get()
        return out
    
    def _call_build_serial_object(self):
        """This function just calls get_serial_object and assigns its value to self.serial_object"""
        self.serial_object = None
        # Make cosmetic changes before any return's get invoked:
        if not self.no_serial:
            print("Opening "+self.serial_selected.get()+" for \""+self.name+"\"")
            self.serial_menu.configure(state='disabled')
        try:
            self.serial_object = self.build_serial_object()
        except Exception as e:
            print("Nurrr")
            try:
                print("Error establishing serial connection to "+self.serial_selected.get()+":")
                print(e)
            except:
                print("Error establishing serial connection to "+self.name+":")
                print(e)
            self.serial_object=None
        if not self.no_serial and self.serial_object is None: #Serial object being none is taken as a proxy for failure
            self.on_serial_open(False)
            self.serial_status.set("Connection Failed")

    def build_serial_object(self):
        """This function constructs whatever object represents a serial connection. By default, it returns None if self.no_serial==True, 
        the shared serial object if self.serial_shared==True, a serial emulator if self.parent_dashboard.use_serial_emulators==True, 
        and otherwise a newly-created Pyserial Serial object with default parameters. However, you can 
        overwrite this function to return a custom serial object (e.g. a PyModbus or MinimalModbus object). The returned object will be stored in self.serial_object.
        
        It's important to actually return something if the connection was initialized successfully, 
        since a number of other methods interpret self.serial_object==None to mean that serial is disconnected or failed to open. If an exception is raised in 
        this method, it'll be handled the same way as a failed handshake, i.e. by calling self.on_serial_open(success=False) and printing the error to console.

        :return: Some kind of serial object for the widget to store and use
        :rtype: Serial, None, or other Object
        """
        # Open serial connection
        if (not self.parent_dashboard.use_serial_emulators) and (not self.no_serial) and (not self.serial_shared):
            return serial.Serial(self.serial_selected.get(),baudrate=self.baudrate,timeout=0)
        elif self.no_serial:
            return None
        elif self.serial_shared:
            return self.widget_to_share_serial_with.get_serial_object()
        elif self.parent_dashboard.use_serial_emulators:
            return self.construct_serial_emulator()
        # It's ok if this raises an error, as it'll get handled in _build_serial_object

    def on_serial_open(self,success):
        """This function is called whenever serial communication is opened, after the serial connection has been queried and 
        its first response has been read. It usually should be overridden in a subclass implementation. The first response is read by on_serial_read, which should return True if the response 
        was valid and False if not; that boolean is then passed to this on_serial_open function.\n

        The intent is that on_serial_open handles any GUI updates required on a successful or unsuccessful 'handshake' with the physical device. 
        In practice, this usually means updating the widget's readout fields to "connection failed" if success=False.

        :param success: True if a serial connection was successfully opened and the expected response was received; False if the serial connection failed or an unexpected response was received.
        :type success: bool
        """
        pass

    def on_handshake_query(self): #This function gets called whenever the widget makes the first query to its serial port
        """This function gets called whenever the widget makes the first query to its serial port. It should send a query whose response on_handshake_read() will parse. 
        By default, it just sends a normal query, but this can be overridden with a custom handshake."""
        print("Device '"+self.name+"' has no handshake defined; just using a standard query/read cycle. See on_handshake_read docs.")
        self.on_serial_query()

    def on_handshake_read(self): #This function gets called a little while after on_handshake_query
        """This function gets called a little while after on_handshake_query to parse the device's response.
        By default, it just does a normal read, but this can be overridden to parse a custom handshake's response. 
        If used as the handshake read (default behavior), this function should return True or nothing if the response is valid and return a string error message or raise an exception 
        if the response was invalid. Returning nothing is interpreted as a successful handshake.
        If on_handshake_read is overridden in the subclass implementation, it's OK for this to return None.
        
        :return: True if the handshake succeeded, False or an error string if not
        :rtype: bool, str, or None"""
        result = self.on_serial_read()
        if result is None:
            return True
        else:
            return result

    def on_serial_query(self): #This function gets called whenever the device queries its serial port
        """This function gets called once every polling interval when the dashboard prompts each device to query its serial connection for updates. 
        It should be overridden in a subclass implementation; if not, it prints a warning."""
        print("Warning: on_serial_query called with no on_serial_query function defined for '"+str(self.name)+"'.")

    def on_serial_read(self): #This function gets called whenever the device reads from its serial port
        """This function gets called once every polling interval when the dashboard prompts each device to check its serial connection for a response to its previous query. 
        It should be overridden in a subclass implementation; if not, it prints a warning."""
        print("Warning: on_serial_read called with no on_serial_read function defined for '"+str(self.name)+"'.")
        return False

    def on_confirm(self): #This function gets called whenever you hit the confirm button
        """This function gets called whenever a widget's 'confirm' button is pressed, which should result in a command (reflecting the latest entries in user input fields) getting sent through the serial connection. 
        This method should be overridden in a subclass implementation, unless the widget has no user input fields. If it's called without being implemented in the subclass, a warning is printed."""
        print("Warning: on_confirm called with no on_confirm function defined for '"+str(self.name)+"'.")

    def on_serial_close(self):
        """This function gets called whenever serial connections are closed. It should be overridden in a subclass implementation. 
        Usually, this function sets readout fields to something like 'no reading' after serial communications are closed."""
        pass

# Methods to support autogenerating menus and readouts from a dict of Tkinter string objects

    def add_field(self, field_type, name, label, default_value, **kwargs):
        """Adds a field (i.e., a text entry box, a dropdown menu, or a text display) to the widget.\n
        
        Adding a field is like making an instance variable for the widget, 
        except 1) the GUI elements get autogenerated for you and 2) fields' values are, by default, logged whenever the dashboard's data logging is active. 
        This method is meant to streamline adding input and output fields, though you can of course define your own instance variables, configure data logging, 
        and add GUI elements by hand to the tkinter frame from widget.get_frame() if you want more granular control. Underlying each field is a tkinter StringVar bound to some tkinter GUI element.\n

        If you add the first input field to a widget, a 'Confirm' button will also automatically be generated and placed. Use the move_confirm_button method to change its location.

        :param field_type: Valid options are 'text output', 'text input', or 'dropdown'
        :type field_type: str
        :param name: The name of the field, which will be used to identify it for automation and for data logging
        :type name: str
        :param label: The text label that will appear to the left of the field. This may differ from the name if you want to include units or abbreviate the label; e.g., the name might be 'Temperature' and the label might be 'Temp. (C)'. If this argument is '' (an empty string), no label is added.
        :type label: str
        :param default_value: The starting value that appears in the field
        :type default_value: str
        :param options: The options in the dropdown option menu. Required if field_type is 'dropdown', ignored otherwise.
        :type options: list, optional
        :param log: Whether or not to log this field's contents when the dashboard's data logging is active. Defaults to True.
        :type log: bool, optional
        :param custom_stringvar: If you want to pass a pre-existing tkinter StringVar to be bound to the field's GUI element, rather than letting this method initialize a new one.
        :type custom_stringvar: tkinter.StringVar, optional

        """
        # Generate the stringvar that will represent this field
        if not ('custom_stringvar' in kwargs.keys()):
            stringvar_to_add = StringVar()
            if default_value is not None:
                stringvar_to_add.set(default_value)
        else:
            stringvar_to_add = kwargs['custom_stringvar']
        # Generate the Tkinter label and widget
        label_to_add = Label(self.frame,text=label)
        if field_type=='text output':
            item_to_add = Label(self.frame,width=10,textvariable=stringvar_to_add)
            self.default_values[name]=default_value
        elif field_type=='text input':
            item_to_add = Entry(self.frame,width=5,textvariable=stringvar_to_add)
        elif field_type=='dropdown':
            if not ('options' in kwargs.keys()):
                raise Exception("Missing required 'options' argument with dropdown items")
            item_to_add = OptionMenu(self.frame, stringvar_to_add, *kwargs['options'])
        else:
            raise Exception("Valid field types are 'text output','text input', or 'dropdown'")
        # Grid them in the widget
        if ('row' in kwargs.keys()) and ('column' in kwargs.keys()):
            row = kwargs['row']
            col = kwargs['column']
        else:
            row = self.frame.grid_size()[1]
            col=0
        if label!='':
            label_to_add.grid(row=row,column=col,sticky='nesw')
        item_to_add.grid(row=row,column=col+1,sticky='nesw')
        # Add the stringvars to the dicts
        if name in self.attributes.keys():
            print("Warning: duplicate attribute '"+str(name)+"' in "+str(self.name))
        self.attributes[name]=stringvar_to_add
        if not (('log' in kwargs.keys()) and (kwargs['log']==False)):#Default behavior is to log data
            self.values_to_log[name]=stringvar_to_add
        # Add the GUI objects to the dict
        self.field_gui_objects[name]=(label_to_add,item_to_add)
        # Add a confirm button if needed
        if (field_type=='text input' or field_type=='dropdown') and not self.confirm_button_added:
            self.confirm_button = Button(self.frame,text=" Confirm ",command=self.confirm)
            self.confirm_button_added=True
            self.confirm_button.grid(row=2,column=2,sticky='nesw')
        # Return the stringvar
        return stringvar_to_add

    def get_field(self, which_field): 
        """Get the current value of the specified field.
        
        :param which_field: The name of the field whose value to get.
        :type which_field: str
        :return: The current value of the specified field
        :rtype: str
        """
        return self.attributes[which_field].get()

    def set_field(self, which_field, new_value):
        """Set the value of the specified field to a specified value.
        
        :param which_field: The name of the field whose value to set.
        :type which_field: str
        :param new_value: The value to which to set the specified field.
        :type new_value: str
        """
        self.attributes[which_field].set(new_value)

    def disable_field(self, which_field):
        """Grey out an input field so that it can't be interacted with.
        
        :param which_field: The name of the field that will be greyed out.
        :type which_field: str
        """
        self.field_gui_objects[which_field][1].configure(state='disabled')

    def enable_field(self, which_field):
        """Un-grey out an input field that had previously been greyed out, allowing it to be interacted with again.
        
        :param which_field: The name of the field to re-enable.
        :type which_field: Str
        """
        self.field_gui_objects[which_field][1].configure(state='normal')

    def move_confirm_button(self,row,column):
        """Move the confirm button, which is automatically placed when using the add_field method to add an input field.
        
        :param row: The row at which to place the confirm button, indexed from 0
        :type row: int
        :param column: The column at which to place the confirm button, indexed from 0
        :type column: int
        """
        self.confirm_button.grid_remove()
        self.confirm_button.grid(row=row,column=column,sticky='nesw')

    def override_color(self,new_color):
        """Manually change the color of a widget's frame to something besides its default defined in its constructor.
        
        :param new_color: The new color, in hex, e.g. '#FF00FF'
        :type new_color: str"""
        self.frame.configure(highlightbackground=new_color,highlightcolor=new_color)

# Underlying methods to make the serial functionality work

    def confirm(self): 
        """Method executed when the Confirm button is pressed. Checks whether serial is connected and unfocuses any input field that's focused, then 
        calls the on_confirm method that is hopefully defined in a subclass."""
        self.parent_dashboard.get_tkinter_object().focus()
        if self.serial_object == None and not self.no_serial:
            print("\"Confirm\" pressed for "+str(self.name)+" with no serial connection.")
            return
        self.on_confirm()

    def open_serial(self):
        """Method executed when serial is opened. Calls open_serial_query and then queues a call to open_serial_read after the necessary amount of time."""
        try:
            self.sending_queue=[]
            self.queue_delays=[]
            self._open_serial_query()
            self._update_cycle_counter=int(self.update_every_n_cycles*4/5)#Force an update the next cycle
            time_to_wait = int((self.parent_dashboard._serial_control_widget.serial_polling_wait)*(int(self.update_every_n_cycles*4/5)+0.5))
            self.parent_dashboard.get_tkinter_object().after(time_to_wait,lambda: self._open_serial_read())
        except Exception as e:
            print("Error in user-defined on_handshake_query or on_serial_query function:")
            print(traceback.format_exc())
            pass

    def _open_serial_query(self):
        """Calls query_serial for the first time."""
        self._update_cycle_counter=-1#Ensure that a query gets made the first time this method runs
        self.on_handshake_query()

    def _open_serial_read(self):
        """Calls the read_serial method, passing the result (a bool of whether the handshake was successful) to the on_serial_open method that is hopefully defined in a subclass implementation. 
        Warns if read_serial (and, equivalently, the subclass-defined on_serial_read method) has not returned the handshake result. Sets serial readouts as needed."""
        if self.serial_object == None and (not self.no_serial):
            return
        try:
            handshake_success = self.on_handshake_read()
        except Exception as e:
            handshake_success = str(e)
        try:
            if handshake_success is True:
                print("Handshake successful on '"+str(self.name)+"'")
            else:
                if handshake_success is False:
                    print("Handshake failed on '"+str(self.name)+"'")
                else:
                    print("Handshake failed on '"+str(self.name)+"' with message: "+str(handshake_success))
                if not self.no_serial:
                    self.serial_status.set("No device found.")
                    try:
                        self.serial_object.close()
                    except:
                        pass
                    self.serial_object = None
            self.on_serial_open(handshake_success)
            if handshake_success is True and not self.no_serial:
                self.serial_status.set("Connected.")
        except Exception as e:
            print("Error in user-defined on_serial_open function in '"+str(self.name)+"': ")
            print(traceback.format_exc())

    def query_serial(self):
        """Executes every time the widget is prompted to query serial. Checks whether to query this cycle, checks whether 
        serial is connected, and then calls the on_serial_query method that is hopefully defined in a subclass implementation."""
        self._update_cycle_counter+=1 #Some devices may only update every 2nd or 3rd cycle
        self._update_cycle_counter%=self.update_every_n_cycles
        if self._update_cycle_counter!=0:
            return
        if self.serial_object == None and (not self.no_serial):
            return
        try:
            self.on_serial_query()
        except Exception as e:
            print("Error in user-defined on_query_serial function in '"+str(self.name)+"': ")
            print(traceback.format_exc())

    def read_serial(self):
        """Executes every time the widget is prompted to read serial. Checks whether to read this cycle, checks whether 
        serial is connected, and then calls the on_serial_read method that is hopefully defined in a subclass implementation. Returns whatever 
        on_serial_read returned, which should be a bool representing whether a valid response was read.\n
        
        If the device updates every n cycles, serial reads always happen 0.5+int(n*4/5) cyles after the serial query; i.e., if n=1, the serial read happens
        0.5 cycles after the query, if n=2, 1.5 after, if n=3, 2.5 after, if n=10, 8.5 after. This is meant to give the instrument a fairly long time to respond where n>1.
        
        :return: Whatever on_serial_read() returned; should be True if a valid serial response was read and False otherwise.
        :rtype: bool
        """
        if (self._update_cycle_counter!=int(self.update_every_n_cycles*4/5)):#Some devices may only update every nth cycle. Suppos
            return
        if self.serial_object == None and (not self.no_serial):
            return
        try:
            val = self.on_serial_read()
            return val
        except Exception as e:
            print("Error in user-defined on_read_serial function in '"+str(self.name)+"': ")
            print(traceback.format_exc())
            return False # A valid response wasn't read, or another error occurred

    def close_serial(self):
        """Closes the serial object, if needed, and returns the GUI fields to their default non-connected states. Executes on_serial_close, which is hopefully implemented in a subclass."""
        if (self.serial_object != None) and not (self.serial_shared):
            try:
                self.serial_object.close()
                self.serial_object = None
            except Exception:
                pass
            try:
                print("Closing "+self.serial_selected.get()+" for \""+self.name+"\"")
            except:
                pass
        if not self.no_serial:
            self.serial_menu.configure(state='normal')
            self.serial_status.set("Not connected.")
        try:
            for k in self.default_values.keys(): #Return text outputs to default value on disconnect
                self.attributes[k].set(self.default_values[k])
            self.on_serial_close()
        except Exception as e:
            print("Error in user-defined on_serial_close function in '"+str(self.name)+"': ")
            print(traceback.format_exc())

    def _update_queue(self):
        """Internal method that sends the next message in a serial write queue and tees up the next call to itself after the specified delay."""
        try:
            self.serial_object.write(self.sending_queue[0])
        except Exception as e:
            self.sending_queue=[]
            self.queue_delays=[]
            return #Serial object has closed in the meantime
        self.sending_queue.pop(0)
        self.queue_delays.pop(0)
        if len(self.sending_queue)!=0:
            self.parent_dashboard.get_tkinter_object().after(self.queue_delays[0],lambda: self._update_queue())

    def send_via_queue(self,text,delay):
        """Add a message to the outgoing serial queue, to be sent a given delay after the next-most-recent message in the queue is sent. 
        If the queue is empty, the message gets sent after the given delay relative to when it was added to the queue. 
        If the widget is sharing serial with another widget, the message gets added to the parent widget's serial queue. 
        Note however that this doesn't work super well with widgets that share serial; queries' orders can get scrambled.
        
        :param text: The message to send to serial, as ascii-encoded bytes
        :type text: bytes
        :param delay: The delay after which to send the text, in milliseconds
        :type column: int
        """
        if self.serial_shared:
            self.widget_to_share_serial_with.send_via_queue(text,delay)
        self.sending_queue.append(text)
        self.queue_delays.append(delay)
        if len(self.sending_queue)==1:
            self.parent_dashboard.get_tkinter_object().after(delay,lambda: self._update_queue())

# Methods related to serial emulators for testing

    def construct_serial_emulator(self):
        """Construct a serial emulator object to facilitate offline testing. Warns if this method is not overridden and hence no serial emulator for this class has been defined.
        
        :return: A serial emulator object for this widget type
        :rtype: pyopticon.generic_serial_emulator.GenericSerialEmulator
        """
        print("Warning: tried to launch a serial emulator when none is defined in "+str(self.name))        
        return None

# Down here are utility methods that you shouldn't need to update for new classes

    def get_serial_object(self):
        """Get the serial object that this widget is using
        
        :return: This widget's serial object, which is probably a Pyserial Serial object, though it could be None or a serial emulator
        :rtype: serial.Serial
        """
        return self.serial_object

    def show_serial(self):
        """Show the serial port selector and status GUI elements, if they were hidden"""
        if self.no_serial:
            return
        self.serial_readout_label.grid()
        self.serial_readout.grid()
        self.serial_menu_label.grid()
        self.serial_menu.grid()

    def hide_serial(self):
        """Hide the serial port selector and status GUI elements"""
        if self.no_serial:
            return
        self.serial_readout_label.grid_remove()
        self.serial_readout.grid_remove()
        self.serial_menu_label.grid_remove()
        self.serial_menu.grid_remove()

    def update_serial_ports(self, new_serial_options):
        """Update the dropdown list of available serial ports
        
        :param new_serial_options: The new list of available serial ports
        :type new_serial_options: list
        """
        if self.no_serial or self.serial_shared:
            return
        self.serial_options = new_serial_options
        prev_value=self.serial_selected.get()
        self.serial_menu.grid_forget()
        self.serial_menu = OptionMenu(self.frame, self.serial_selected, *self.serial_options)
        self.serial_menu.grid(row=1,column=1,sticky='nesw')
        self.serial_selected.set(prev_value)
    
    def get_frame(self):
        """Get the tkinter frame on which this object is drawn.
        
        :return: The widget's tkinter frame
        :rtype: tkinter.Frame
        """
        return self.frame


