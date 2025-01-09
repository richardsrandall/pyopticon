# Import these for all dashboard objects
#from tkinter import *
from tkinter import Tk, font
import sys
import threading
from ._system._show_hide_widget import ShowHideWidget
from ._system._serial_widget import SerialWidget
from ._system._automation_widget import AutomationWidget
from ._system._data_logging_widget import DataLoggingWidget
from ._system._socket_widget import SocketWidget
import datetime
import traceback


class PyOpticonDashboard:
    """ A Dashboard is our term for a GUI window containing various 'widgets'. A standalone program should initialize, configure, and run each dashboard. 
    One dashboard may contain many widgets, each representing a physical device or some other functionality.\n

    See the tutorials for examples of initializing and populating a dashboard. Generally, the workflow is to:

    - Initialize a dashboard
    - Initialize widgets and add them to the dashboard
    - Define any desired interlocks and add them to the dashboard
    - Launch the dashboard

    :param dashboard_name: The name of the dashboard, which appears in any data logging files that the dashboard creates.
    :type dashboard_name: str
    :param offline_mode: Defaults to False. If True, doesn't attempt to build any serial.Serial objects, and widgets may also check to behave differently.
    :type offline_mode: bool, optional
    :param polling_interval_ms: The interval for polling all connected devices, in milliseconds. Defaults to 1000. You may want to use a larger interval if certain devices are slow to poll, or polling them involves blocking code (not recommended).
    :type polling_interval_ms: int, optional
    :param window_resizeable: Whether or not you can manually resize the dashboard by dragging and dropping the corner. Defaults to false. If True, the window is resizeable, but the widgets don't scale or center themselves.
    :type window_resizeable: bool, optional
    :param persistent_console_logfile: Whether or not to log console events to a persistent file (same throughout multiple dashboard relaunches) in the same directory as the dashboard initialization script.
    :type persistent_console_logfile: bool, optional
    :param print_stacktraces: If true, exception stack traces are printed to console; if false, only to the logfile. Exception names are printed regardless.
    :type print_stacktraces: bool, optional
    :param x_pad: The horizontal pad between widgets, in pixels.
    :type x_pad: int, optional
    :param y_pad: The vertical pad between widgets, in pixels.
    :type y_pad: int, optional
    :param socket_ports: A list of integer ports on which to open sockets for client connections. Defaults to [12345].
    :type socket_ports: list, optional
    :param include_auto_widget: Whether or not to display an automation widget on the dashboard.
    :type include_auto_widget: bool, optional
    :param include_socket_widget: Whether or not to display a socket widget on the dashboard.
    :type include_socket_widget: bool, optional

    """

    def __init__(self, dashboard_name, **kwargs):
        """Constructor for a Dashboard object."""

        # Unpack kwargs
        offline_mode = False if not 'offline_mode' in kwargs.keys() else kwargs['offline_mode']
        polling_interval_ms = 1000 if not 'polling_interval_ms' in kwargs.keys() else kwargs['polling_interval_ms']
        window_resizeable = False if not 'window_resizeable' in kwargs.keys() else kwargs['window_resizeable']
        persistent_console_logfile = True if not 'persistent_console_logfile' in kwargs.keys() else kwargs['persistent_console_logfile']
        x_pad = 50 if not 'x_pad' in kwargs.keys() else kwargs['x_pad']
        y_pad = 25 if not 'y_pad' in kwargs.keys() else kwargs['y_pad']
        self.print_stacktraces = True if not 'print_stacktraces' in kwargs.keys() else kwargs['print_stacktraces']
        socket_ports = [12345] if not 'socket_ports' in kwargs.keys() else kwargs['socket_ports']
        self.include_auto_widget = True if not 'include_auto_widget' in kwargs.keys() else kwargs['include_auto_widget']
        self.include_socket_widget = True if not 'include_socket_widget' in kwargs.keys() else kwargs['include_socket_widget']
        if not self.include_socket_widget:
            socket_ports = [] # Prevents any socket threads from getting launched
        
        self.name = dashboard_name
        root = Tk()
        self.root = root
        window_title="PyOpticon 0.2.0"
        self.title = window_title
        root.title(window_title)
        self.offline_mode = offline_mode
        self.window_resizeable=window_resizeable
        self.persistent_console_logfile=persistent_console_logfile

        self.x_pad = x_pad
        self.y_pad = y_pad

        # Setup widget storage
        self.all_widgets = []
        self.widgets_by_nickname = dict()
        self.all_widget_names = []

        # Add a list of interlocks (functions)
        self.all_interlocks = []

        # Create a serial control widget
        self.serial_connected = False
        self._serial_control_widget = SerialWidget(self, polling_interval_ms)
        self._serial_control_widget.get_frame().grid(row=0,column=0,padx=self.x_pad,pady=self.y_pad)

        # Control widget for showing and hiding things
        self._show_hide_control_widget = ShowHideWidget(self)
        self._show_hide_control_widget.get_frame().grid(row=1,column=0,padx=self.x_pad,pady=self.y_pad)

        i=2 #To facilitate option to get rid of sockets / automation widgets

        # Control widget for running scripts. If not included, the object is created but never displayer.
        self._automation_control_widget = AutomationWidget(self)
        if self.include_auto_widget:
            self._automation_control_widget.get_frame().grid(row=i,column=0,padx=self.x_pad,pady=self.y_pad)
            i+=1
            self.all_widgets.append(self._automation_control_widget)

        # Create a widget for socket control. If not included, the object is created but never displayed.
        self._socket_widget = SocketWidget(self,socket_ports)
        if self.include_socket_widget:
            self._socket_widget.get_frame().grid(row=i,column=0,padx=self.x_pad,pady=self.y_pad)
            i+=1

        # Control widget for data logging
        self._logging_control_widget = DataLoggingWidget(self)
        self._logging_control_widget.get_frame().grid(row=i,column=0,padx=self.x_pad,pady=self.y_pad)
        i+=1
    
    def add_widget(self, widget, row, column):
        """Add a widget to the dashboard at the specified row and column, each indexed from 0. 
        Note that rows 0-3 in column 0 are reserved for the four dashboard control widgets. 
        If the specified grid coordinates are already occupied, add_widget hides the 
        widget that was there before. It warns to console if the widget added shares a name or nickname with an existing widget.

        :param widget: The widget to add to the dashboard
        :type widget: pyopticon.generic_widget.GenericWidget or pyopticon.minimal_widget.MinimalWidget
        :param row: The row in the dashboard's Tkinter grid at which to place the widget, indexed from 0
        :type row: int
        :param column: The column in the dashboard's Tkinter grid at which to place the widget, indexed from 0
        :type column: int
        """
        widget.get_frame().grid(row=row, column = column, padx=self.x_pad,pady=self.y_pad)
        self.all_widgets.append(widget)
        if hasattr(widget,'name'):
            if widget.name in self.all_widget_names:
                print("Warning: adding a widget with a duplicate name '"+str(widget.name)+"'. Data logging issues may result. Best practice is to use distinct names.")
            self.all_widget_names.append(widget.name)
        if hasattr(widget,'nickname'):
            if widget.nickname in self.widgets_by_nickname.keys():
                print("Warning: adding a widget with a duplicate nickname '"+str(widget.nickname)+"'. Automation issues may result. Best practice is to use distinct nicknames.")
            self.widgets_by_nickname[widget.nickname] = widget

    def add_interlock(self, fn):
        """Add an interlock function that will be called once every polling cycle.\n
        
        You'll probably want to define such a function in the same file where the dashboard is constructed. 
        You can use the dashboard's get_field and/or get_widgets_by_nickname methods to check whether 
        the system state violates a certain interlock condition (e.g., a certain temperature reading is too high), 
        and then respond accordingly (e.g., use the dashboard's set_field method to shut off the flow of reactive gases, or 
        use the gmail_helper module to email or text the operator that something has gone wrong).

        :param fn: The interlock function to add. Should take no arguments and return nothing.
        :type fn: function
        """
        self.all_interlocks.append(fn)
    
    def start(self):
        """Launch the dashboard, including all necessary threads."""

        # Open a persistent logfile
        if self.persistent_console_logfile:
            console_logfile = open("persistent_logfile.txt", "a")
            console_logfile.write("\n")
        else:
            console_logfile = None
        self.console_logfile = console_logfile

        # Digression while we define a class that's used to replace stdout with the desired logging behavior
        # Start function resumes afterwards.
        # Override stdout to something threadsafe (ish) that also includes logging to a .txt logfile, if desired, and timestamps in all printouts
        class threadsafe_print(object):
            def __init__(self): #Initialize and save original stdout
                self.stdout = sys.stdout
            def write(self, s):# Default write
                if s!="\n":
                    self.stdout.write(str(datetime.datetime.now().strftime("%H:%M:%S"))+": "+str(s)+"\n")
                    if console_logfile is not None:
                        try:
                            console_logfile.write(str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+": "+str(s)+"\n")
                        except Exception as e:
                            pass #File got closed while we weren't looking.
            def flush(self):#Called on program close, so need to have
                pass
                        
            def write_console_only(self, s): # Used in my code's exception handler
                self.stdout.write(str(datetime.datetime.now().strftime("%H:%M:%S"))+": "+str(s)+"\n")
                
            def write_logfile_only(self,s): # Used in my code's exception handler
                try:
                    console_logfile.write(str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+": "+str(s)+"\n")
                except Exception as e:
                    pass #File got closed while we weren't looking.

        # Override the Tkinter error reporter to the dashboard's error handler
        def report_callback_exception(exc, val, tb):
            self.exc_handler(val,'system')
        self.root.report_callback_exception = report_callback_exception
                
        self.print_obj = threadsafe_print()
        sys.stdout = self.print_obj
        print("Dashboard launched.")

        # Launch some other threads!
        for widget in self.all_widgets:
            if hasattr(widget,'_run_thread'):
                threading.Thread(target=widget._run_thread).start()

        # Preparations to launch the Tkinter mainloop
        if not self.window_resizeable:
            self.get_tkinter_object().after(100, lambda: self.get_tkinter_object().resizable(False,False))
        self._serial_control_widget._update_serial_ports()
        def on_close():
            if self.serial_connected:
                self._serial_control_widget._toggle_serial_connected()
            self.get_tkinter_object().destroy()    
        self.get_tkinter_object().protocol("WM_DELETE_WINDOW", on_close)
        
        # Start polling the sockets, creating as many threads as are needed
        for p in self._socket_widget.port_numbers:
            threading.Thread(target=self._socket_widget._run_one_thread,args=(p,)).start()

        # Launch the mainloop
        self.get_tkinter_object().mainloop()

        # Shutdown the threads
        self.serial_connected=False
        for widget in self.all_widgets:
            if hasattr(widget,'_shutdown_thread'):
                widget._shutdown_thread()
        self._socket_widget._shutdown_threads()
        print("Dashboard closed normally.")
        if self.persistent_console_logfile:
            console_logfile.close()

    def exc_handler(self,exc,source='system',widget=None):#Function used in various places to print helpful info about exceptions 
        """Handle an exception according to the protocol configured when the dashboard was launched. Generate a 
        message about what subprocess raised the exception.
        
        :param exc: The Exception being raised
        :type exc: Exception
        :param source: The source of the exception according to a scheme outlined in the if-statement in the function definition. Defaults to 'system'.
        :type source: str, optional
        :param widget: The nickname of the widget that raised the exception, if applicable
        :type widget: str, optional

        """
        if source=='system':
            source_str='internal PyOpticon code'
        elif source=='on_serial_open_failure':
            source_str="user-defined 'on_failed_serial_open' method"
        elif source=='on_handshake':
            source_str="user-defined 'on_handshake' method treated as failed handshake"
        elif source=='on_update':
            source_str="user-defined 'on_update' method"
        elif source=='on_serial_close':
            source_str="user-defined 'on_serial_close' method"
        elif source=='on_confirm':
            source_str="user-defined 'on_confirm' method"
        elif source=='automation':
            source_str="user-supplied automation script execution"
        elif source=='automation await':
            source_str="user-supplied automation await condition (script will not advance)"
        elif source=='socket':
            source_str="user-supplied socket command execution"
        elif source=='serial build':
            source_str="system initialization of serial.Serial object"
        else:
            source_str=source
        if widget is not None:
            source_str = source_str+" in '"+widget+"'"
        
        msg = 'Exception in '+source_str+': '+str(exc)
        info = "\n"+traceback.format_exc()
        if self.print_stacktraces:
            print(msg+info)
        else:
            self.print_obj.write_console_only(msg)
            if self.persistent_console_logfile:
                self.print_obj.write_logfile_only(msg+info)
            

    def check_offline_mode(self):
        """Check whether dashboard is in offline mode.
        
        :return: Whether the dashboard is in offline mode.
        :rtype: bool
        return self.offline_mode
        """

    def check_serial_connected(self):
        """Check whether serial is currently connected
        
        :return: Whether the dashboard's serial is connected.
        :rtype: bool
        """
        return self.serial_connected

    def get_field(self,target_widget_nickname, target_field):
        """Get the current value of a certain field of a certain widget. The field must have been created with the 
        add_field method of the GenericWidget class. To access an instance variable of a widget, use get_widget_by_nickname instead. 
        To see a list of widgets' nicknames and fields, run the dashboard and use the 'automation help' button.

        :param target_widget_nickname: The nickname of the widget
        :type target_widget_nickname: str
        :param target_field: The name of the field to read
        :type target_field: str
        :return: The value of the field that you queried
        :rtype: str
        """
        return self.widgets_by_nickname[target_widget_nickname].get_field(target_field)
    
    def set_field(self,target_widget_nickname, target_field, new_value, confirm=True):
        """Set the value of a certain field of a certain widget and, optionally, execute the widget's confirm function. 
        The field must have been created with the add_field method of the GenericWidget class. 
        To modify an instance variable of a widget, use get_widget_by_nickname instead. 
        To see a list of widgets' nicknames and fields, run the dashboard and use the 'automation help' button. 

        :param target_widget_nickname: The nickname of the widget
        :type target_widget_nickname: str
        :param target_field: The name of the field to modify
        :type target_field: str
        :param new_value: The new value for the field. Fields' values are always stored as strings, even if they represent numbers.
        :type new_value: str
        :param confirm: Whether or not to execute the widget's confirm function, which usually sends a command to the physical device based on the newly updated field.
        :type confirm: bool
        """
        self.widgets_by_nickname[target_widget_nickname].set_field(target_field,new_value)
        if confirm:
            self.widgets_by_nickname[target_widget_nickname].confirm()

    def get_widget_by_nickname(self, nickname):
        """Get a certain widget based on its nickname. 
        To see a list of widgets' nicknames and fields, run the dashboard and use the 'automation help' button.

        :param target_widget_nickname: The nickname of the widget
        :type target_widget_nickname: str

        :return: The corresponding widget
        :rtype: pyopticon.generic_widget.GenericWidget or pyopticon.minimal_widget.MinimalWidget
        """
        return self.widgets_by_nickname[nickname]
    
    def get_widgets_by_nickname(self):
        """Get a dict that maps widgets' nicknames to the corresponding widget objects. Widgets that were added with no or None nicknames are excluded. 

        :return: A dict mapping nicknames (str) to widgets (GenericWidget)
        :rtype: dict
        """
        return self.widgets_by_nickname
    
    def get_tkinter_object(self):
        """Get the dashboard's Tkinter frame object, through which Tkinter functions like after() can be accessed.

        :return: The dashboard's Tkinter frame object.
        :rtype: tkinter.Tk
        """
        return self.root
    
    def scale_all_text(self,scale_factor):
        """Go through all the widgets and scale the font on any tkinter Label, Text, OptionMenu, or Button objects. 
        Meant as a quick fix for using dashboards on smaller or larger screems.
        
        :param scale_factor: A factor by which to scale text, e.g. 1.2. Values are calculated in font units and are rounded to the nearest int.
        :type scale_factor: float
        """
        system_widgets=[self._automation_control_widget,self._logging_control_widget,self._serial_control_widget,self._show_hide_control_widget]
        # Scale all the font sizes; only do it once for each font
        fonts_done = set()
        for widget in self.all_widgets+system_widgets:
            frame = widget.get_frame()
            for child in frame.winfo_children():
                #print(type(child))
                s = str(type(child))
                if ('tkinter.Label' in s) or ('tkinter.Button' in s) or ('tkinter.OptionMenu' in s) or ('tkinter.Entry' in s):
                    font_name = child['font']
                    if font_name in fonts_done:
                        continue
                    fonts_done.add(font_name)
                    try:
                        current_font = font.nametofont(font_name)
                    except Exception as e:
                        current_font = font.Font(font=font_name)
                    current_size = int(current_font.cget('size'))
                    new_size = int(current_size*scale_factor)
                    new_size = 1 if new_size<1 else new_size
                    current_font.config(size=new_size)
                    child.config(font=current_font)
            # Adjust the frame thicknesses too
            current_thickness = int(frame.cget('highlightthickness'))
            new_thickness = int(current_thickness*scale_factor)
            new_thickness = 5 if new_thickness<5 else new_thickness
            frame.configure(highlightthickness=new_thickness)
            # Updating every modified widget re-centers the text and stops things from looking wonky
            for child in frame.winfo_children():
                if ('tkinter.Label' in s) or ('tkinter.Button' in s) or ('tkinter.OptionMenu' in s) or ('tkinter.Entry' in s):
                    child.update()
                    
