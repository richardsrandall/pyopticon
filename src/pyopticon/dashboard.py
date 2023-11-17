# Import these for all dashboard objects
#from tkinter import *
from tkinter import Tk, font
from ._system._show_hide_widget import ShowHideWidget
from ._system._serial_widget import SerialWidget
from ._system._automation_widget import AutomationWidget
from ._system._data_logging_widget import DataLoggingWidget

# Asyncio
from async_tkinter_loop import async_mainloop

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
    :param use_serial_emulators: Defaults to False. If False, attempts to connect to physical devices via wired serial connections; if True, attempts to launch a serial emulator for each widget instead.
    :type use_serial_emulators: bool, optional
    :param polling_interval_ms: The interval for polling all connected devices, in milliseconds. Defaults to 1000. You may want to use a larger interval if certain devices are slow to poll, or polling them involves blocking code (not recommended).
    :type polling_interval_ms: int, optional
    :param window_resizeable: Whether or not you can manually resize the dashboard by dragging and dropping the corner. Defaults to false. If True, the window is resizeable, but the widgets don't scale or center themselves.
    :type window_resizeable: bool, optional

    """

    def __init__(self, dashboard_name, use_serial_emulators=False, polling_interval_ms=1000,window_resizeable=False):
        """Constructor for a Dashboard object."""
        self.name = dashboard_name
        root = Tk()
        self.root = root
        window_title="PyOpticon 0.1.7 Alpha"
        self.title = window_title
        root.title(window_title)
        self.use_serial_emulators = use_serial_emulators
        self.window_resizeable=window_resizeable

        self.x_pad = 50
        self.y_pad = 25

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

        # Control widget for running scripts
        self._automation_control_widget = AutomationWidget(self)
        self._automation_control_widget.get_frame().grid(row=2,column=0,padx=self.x_pad,pady=self.y_pad)

        # Control widget for data logging
        self._logging_control_widget = DataLoggingWidget(self)
        self._logging_control_widget.get_frame().grid(row=3,column=0,padx=self.x_pad,pady=self.y_pad)
    
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
        """Launch the dashboard by starting the Tkinter main loop as an asynchronous process using the async_tkinter_loop package. 
        This function blocks until the dashboard is closed."""
        if not self.window_resizeable:
            self.get_tkinter_object().after(100, lambda: self.get_tkinter_object().resizable(False,False))
        self._serial_control_widget._update_serial_ports()
        def on_close():
            if self.serial_connected:
                self._serial_control_widget._toggle_serial_connected()
            self.get_tkinter_object().destroy()    
        self.get_tkinter_object().protocol("WM_DELETE_WINDOW", on_close)
        async_mainloop(self.get_tkinter_object())

    def get_field(self,target_widget_nickname, target_field):
        """Get the current value of a certain field of a certain widget. The field must have been created with the 
        add_field method of the GenericWidget class. To access an instance variable of a widget, use get_widget_by_nickname instead. 
        To see a list of widgets' nicknames and fields, run the dashboard and use the 'automation help' button.

        :param target_widget_nickname: The nickname of the widget
        :type target_widget_nickname: str
        :param target_field: The name of the field to read
        :type target_field: str
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
                    
