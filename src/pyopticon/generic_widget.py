from tkinter import *
import ctypes
import serial
import time
import traceback
import queue

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
    :param color: The color of the widget's frame, as a RGB hex string, e.g. '#00FF00'
    :type color: str
    :param use_serial: True if this widget needs to have a serial connection; False otherwise. Defaults to True.
    :type use_serial: bool, optional
    :param default_serial_port: The name of the default selected serial port, e.g. 'COM9'
    :type default_serial_port: str
    :param default_serial_port: The name of the default selected serial port, e.g. 'COM9'. Required unless no_serial is True.
    :type default_serial_port: str, optional
    :param baudrate: The baud rate of the serial connection, as an integer, e.g. 19200. Required unless no_serial is True or build_serial_object is overridden.
    :type baudrate: int, optional
    :param widget_to_share_thread_with: A widget whose thread this widget will share, rather than creating its own. If use_serial = True, it's assumed the widget will share the serial.Serial object.
    :type widget_to_share_thread_with: pyopticon.generic_widget.GenericWidget, optional
    :param update_every_n_cycles: Set the widget to poll its serial connection for updates every n cycles. Useful for instruments that poll slowly for some reason, or whose state changes infrequently. Defaults to 1.
    :type update_every_n_cycleS: int, optional
    """

    def __init__(self,parent_dashboard,name,nickname,color,**kwargs):
        """Constructor for a GenericWidget"""

        # Required arguments: parent_dashboard, name, nickname, color
        # Optional: use_serial, default_serial_port, baudrate, widget_to_share_thread_with, update_every_n_cycles

        # Unpack basic arguments
        self.name = name
        self.nickname = nickname
        self.serial_object = None

        # Flag for whether initialization and handshake were successful
        self.doing_handshake = False
        self.handshake_was_successful = False

        # Unpack kwargs
        no_serial = (not kwargs['use_serial']) if ('use_serial' in kwargs.keys()) else False
        self.default_serial = kwargs['default_serial_port'] if not no_serial else None
        self.baudrate = kwargs['baudrate'] if ('baudrate' in kwargs.keys()) else None
        update_every_n_cycles = kwargs['update_every_n_cycles'] if ('update_every_n_cycles' in kwargs.keys()) else 1
        widget_to_share_thread_with = kwargs['widget_to_share_serial_with'] if ('widget_to_share_serial_with' in kwargs.keys()) else None
        self.thread_shared = (widget_to_share_thread_with!=None) # Share the serial connection with a previously constructed device
        self.widget_to_share_thread_with=widget_to_share_thread_with
        self.no_serial = no_serial
        self.update_every_n_cycles=update_every_n_cycles
        self._update_cycle_counter=-1

        # Check kwargs
        if not no_serial and self.widget_to_share_thread_with==None:
            if self.default_serial == None:
                raise Exception("Default serial port required unless use_serial==False or thread is shared with other widget.")
            if self.baudrate == None:
                raise Exception("Baud rate required unless use_serial == False or thread is shared with other widget.")


        # Create a frame, set its style
        self.color = color
        self.frame = Frame(parent_dashboard.get_tkinter_object(), highlightbackground=self.color, highlightcolor=self.color, highlightthickness=5)
        self.parent_dashboard = parent_dashboard
        
        # Create the title
        Label(self.frame,text=name).grid(row=0,column=1)
        
        if not no_serial:
            # Labels associated with serial communications
            if not self.thread_shared:
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
            if not self.thread_shared:
                self.serial_menu = OptionMenu(self.frame, self.serial_selected, *self.serial_options)
            else:
                self.serial_menu = Label(self.frame,text=str(self.widget_to_share_thread_with.nickname))
            self.serial_menu.grid(row=1,column=1,sticky='nesw')
            self.serial_readout = Label(self.frame,textvariable=self.serial_status)
            self.serial_readout.grid(row=2,column=1,sticky='nesw')

        # Construct a map of attributes for automation
        self.attributes = dict()
        self.values_to_log = dict()
        self.default_values = dict()
        self.field_gui_objects = dict()
        self.confirm_button_added = False

        # Create a queue for the thread, if needed
        if not self.thread_shared:
            self.queue = queue.Queue()
        else:
            self.queue = widget_to_share_thread_with.queue
        self.doing_update = False
        self.shutdown_flag=False

# Methods implementing serial functionality that will often be overridden by the user

    def on_failed_serial_open(self):
        """This function is called when the Dashboard attempts to open a Serial port and it fails for some 
         reason. It can be used to set the readout fields to 'None' or something, if desired.
        """
        pass

    def on_handshake(self): #This function gets called whenever the widget makes the first query to its serial port
        """This function gets called whenever the widget is initialized. If the widget uses a Serial connection, you can assume 
        that the serial connection was already initialized successfully. If not, you'll need to initialize whatever objects are needed 
        to update the widget in this method (say, an OEM Python driver).
        
        By default, it just calls on_update(), assuming that the handshake was successful if (and only if) no exception was raised."""

        print("Device '"+self.name+"' has no handshake defined; just using a standard update cycle. See on_update docs.")
        self.on_update()
        
    def on_update(self): #This function gets called whenever the device updates itself
        """This function gets called once every polling interval when the dashboard prompts each device to update itself. 
        It should be overridden in a subclass implementation; if not, it prints a warning."""
        print("Warning: on_update called with no on_update function defined for '"+str(self.name)+"'.")

    def on_confirm(self): #This function gets called whenever you hit the confirm button
        """This function gets called whenever a widget's 'confirm' button is pressed, which should result in a command (reflecting the latest entries in user input fields) getting sent through the serial connection. 
        This method should be overridden in a subclass implementation, unless the widget has no user input fields. If it's called without being implemented in the subclass, a warning is printed."""
        print("Warning: on_confirm called with no on_confirm function defined for '"+str(self.name)+"'.")

    def on_serial_close(self):
        """This function gets called whenever serial connections are closed. It should be overridden in a subclass implementation. 
        Usually, this function sets readout fields to something like 'no reading' after serial communications are closed. 
        Note that while the other user-defined methods run in the widget's thread, this method runs immediately in the main 
        GUI thread, ensuring that the serial connection closure happens immediately."""
        pass

# Methods to support autogenerating menus and readouts from a dict of Tkinter string objects and logging their values

    def add_field(self, field_type, name, label, default_value=None, **kwargs):
        """Adds a field (i.e., a text entry box, a dropdown menu, or a text display) to the widget.\n
        
        Adding a field is like making an instance variable for the widget, 
        except 1) the GUI elements get autogenerated for you and 2) fields' values are, by default, logged whenever the dashboard's data logging is active. 
        This method is meant to streamline adding input and output fields, though you can of course define your own instance variables, configure data logging, 
        and add GUI elements by hand to the tkinter frame from widget.get_frame() if you want more granular control. Underlying each field is a tkinter StringVar bound to some tkinter GUI element.\n

        If you add the first input field to a widget, a 'Confirm' button will also automatically be generated and placed. Use the move_confirm_button method to change its location.

        :param field_type: Valid options are 'text output', 'text input', 'dropdown', or 'button'
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
        elif field_type=='button':
            if not('action' in kwargs.keys()):
                raise Exception("Missing required 'action' argument with button")
            item_to_add = Button(self.frame, text=name, command=kwargs['action'])
        else:
            raise Exception("Valid field types are 'text output','text input', 'dropdown', or 'button'")
        
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

    def do_threadsafe(self,to_do):
        """Feeds the specified function to tkinter's after() method with a delay of 0, so that it will be executed in a thread-safe way.
        
        :param to_do: The function to execute.
        :type to_do: function"""
        tkinter_obj = self.parent_dashboard.get_tkinter_object()
        tkinter_obj.after(0,to_do)

    def get_field(self, which_field): 
        """Get the current value of the specified field.
        
        :param which_field: The name of the field whose value to get.
        :type which_field: str
        :return: The current value of the specified field
        :rtype: str
        """
        return self.attributes[which_field].get()

    def set_field(self, which_field, new_value, hush_warning=False):
        """Set the value of the specified field to a specified value.
        
        :param which_field: The name of the field whose value to set.
        :type which_field: str
        :param new_value: The value to which to set the specified field.
        :type new_value: str
        :param hush_warning: Silence the warning when you set a field while a widget's serial isn't connected.
        :type hush_warning: True
        """
        if (not self.parent_dashboard.serial_connected) and (not hush_warning):
            print("Warning: set_field called in '"+self.name+"' while serial is not connected (field: "+which_field+"). Consider checking self.parent_dashboard.serial_connected before calling, or call set_field with hush_warning=True .")
        to_do = lambda: self.attributes[which_field].set(new_value)
        self.do_threadsafe(to_do)

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

# Cosmetic methods to enable/disable fields, move the confirm button, or change the widget color

    def disable_field(self, which_field):
        """Grey out an input field so that it can't be interacted with.
        
        :param which_field: The name of the field that will be greyed out.
        :type which_field: str
        """
        to_do = lambda: self.field_gui_objects[which_field][1].configure(state='disabled')
        self.do_threadsafe(to_do)

    def enable_field(self, which_field):
        """Un-grey out an input field that had previously been greyed out, allowing it to be interacted with again.
        
        :param which_field: The name of the field to re-enable.
        :type which_field: Str
        """
        to_do = lambda: self.field_gui_objects[which_field][1].configure(state='normal')
        self.do_threadsafe(to_do)

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

# Methods to make a thread for this widget (!)
        
    def _run_thread(self):
        """Launch a thread to process commands from the widget's queue. The thread just keeps 
        checking for new commands in its queue forever until the close flag is set. Valid commands 
        are 'UPDATE', 'HANDSHAKE', and 'CONFIRM'."""

        if self.thread_shared: #We post events to a shared queue in a different widget's thread
            pass
        else: #This widget gets its own thread in which to process events
            while True:
                if self.shutdown_flag: # Bail immediately
                    return
                try:
                    while not self.queue.empty():
                        (cmd,widget) = self.queue.get()
                        
                        if cmd == 'UPDATE': # Update the widget however desired
                            self.doing_update = True
                            widget._update()
                            self.doing_update = False # Flag to let us warn if the polling interval is too short

                        elif cmd == 'CONFIRM': # Tell the thread to update the system state
                            widget._on_confirm()

                        elif cmd == 'HANDSHAKE': # Tell the thread to open serial and do the handshake
                            self.doing_handshake = True
                            widget._handshake()
                            self.doing_handshake = False

                except Exception as e:
                    self.parent_dashboard.exc_handler(e,'system',self.name)

                time.sleep(0.05)

    def _shutdown_thread(self):
        """Shutdown the widget's thread once the GUI is closed."""
        self.shutdown_flag = True


# Underlying methods to make the serial functionality work.
# These are generally wrappers around the user-defined methods like on_update, on_handshake, and on_confirm.
# They contain a bunch of functionality that the user likely doesn't want to implement themselves, e.g. 
# building serial objects, complaining if you hit confirm without serial being open, knowing not to build a 
# serial object if use_serial=False, and various other things. Apologies that it's a bit of a mess down here, 
# but since this code has been working fairly reliably for me, I don't really want to mess with it at the moment.
    
    def _build_serial_object(self):
        """This function just calls get_serial_object and assigns its value to self.serial_object"""
        self.serial_object = None
        # Make cosmetic changes before any return's get invoked:
        if not self.no_serial:
            print("Opening "+self.serial_selected.get()+" for \""+self.name+"\"")
            self.serial_menu.configure(state='disabled')
        try:
            if (not self.parent_dashboard.offline_mode) and (not self.no_serial) and (not self.thread_shared):
                self.serial_object = serial.Serial(self.serial_selected.get(),baudrate=self.baudrate,timeout=0)
            elif self.no_serial:
                self.serial_object = None
            elif self.thread_shared:
                self.serial_object = self.widget_to_share_thread_with.get_serial_object()
        except Exception as e:
            self.parent_dashboard.exc_handler(e,'serial build',self.name)
            self.serial_object=None
        if not self.no_serial and self.serial_object is None and not self.parent_dashboard.offline_mode: #Serial object being none is taken as a proxy for failure
            self.on_failed_serial_open()
            return False
        return True

    def confirm(self): 
        """Method executed when the Confirm button is pressed. Checks whether serial is connected and unfocuses any input field that's focused, then 
        calls the on_confirm method that is hopefully defined in a subclass."""
        self.parent_dashboard.get_tkinter_object().focus()
        if self.serial_object == None and not (self.no_serial or self.parent_dashboard.offline_mode):
            print("\"Confirm\" pressed for "+str(self.name)+" with no serial connection.")
            return
        
        if self.doing_handshake:
            print("\"Confirm\" pressed for "+str(self.name)+" while still handshaking.")
            return
        
        self.queue.put(('CONFIRM',self))

    def _on_confirm(self):
        try:
            self.on_confirm()
        except Exception as e:
            self.parent_dashboard.exc_handler(e,'on_confirm',self.name)

    def _update(self):
        """Executes every time the widget is prompted to update. Checks whether to update this cycle, checks whether 
        serial is connected, and then calls the on_update method that is hopefully defined in a subclass implementation."""
        self._update_cycle_counter+=1 #Some devices may only update every 2nd or 3rd cycle
        self._update_cycle_counter%=self.update_every_n_cycles
        if self._update_cycle_counter!=0:
            return
        if not self.handshake_was_successful or self.doing_handshake:
            return
        try:
            self.on_update()
        except Exception as e:
            self.parent_dashboard.exc_handler(e,'on_update',self.name)

    def _handshake(self):
        """Builds the serial object, if needed, and prompts the widget to handshake with the device, handling errors as needed."""

        # Build serial object (if needed)
        if not self.no_serial:
            self.do_threadsafe(lambda: self.serial_status.set("Connecting..."))
        try:
            serial_success = self._build_serial_object()
        except Exception as e:
            serial_success = False
            self.parent_dashboard.exc_handler(e,'serial build',self.name)

        if not serial_success:
            if not self.no_serial:
                self.do_threadsafe(lambda: self.serial_status.set("Connection Failed"))

        if serial_success:
            # Do the handshake
            try:
                self.on_handshake()
                print("Handshake successful for '"+str(self.name)+"'.")
                handshake_success = True
                if not self.no_serial:
                    self.do_threadsafe(lambda: self.serial_status.set("Connected"))
            except Exception as e:
                handshake_success = False
                if not self.no_serial:
                    self.do_threadsafe(lambda: self.serial_status.set("No Device Found"))
                self.parent_dashboard.exc_handler(e,'on_handshake',self.name)
        else:
            handshake_success = False

        # Set the failure flag
        self.handshake_was_successful = serial_success and handshake_success
        if not self.handshake_was_successful:
            self.on_failed_serial_open()


    def close_serial(self):
        """Closes the serial object, if needed, and returns the GUI fields to their default non-connected states. Executes on_serial_close, which is hopefully implemented in a subclass."""
        if (self.serial_object != None) and not (self.thread_shared):
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
            self.parent_dashboard.exc_handler(e,'on_serial_close',self.name)


# Down here are utility methods that you shouldn't need to update for new classes

    def get_serial_object(self):
        """Get the serial object that this widget is using
        
        :return: This widget's serial object, which is probably a Pyserial Serial object.
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
        if self.no_serial or self.thread_shared:
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


