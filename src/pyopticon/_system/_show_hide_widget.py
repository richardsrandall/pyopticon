from tkinter import *
import ctypes
from tkinter import messagebox
import webbrowser


# Show and hide widget
class ShowHideWidget:
    """ This widget contains buttons to show/hide the console (on PC's), show/hide all the other widgets' serial controls, 
    print automation help to the console, and open help/tutorials.

    :param parent: The dashboard to which this widget will be added.
    :type parent: pyopticon.dashboard.Dashboard
    """

    def __init__(self, parent_dashboard):
        """The constructor for the ShowHideWidget"""
        self.parent = parent_dashboard
        self.root = parent_dashboard.get_tkinter_object()
        self.main_color = '#FF7F7F'
        # Widget for showing and hiding terminal and serial interfaces
        self.frame = Frame(self.root,highlightbackground=self.main_color, highlightcolor=self.main_color, highlightthickness=5)
        Label(self.frame,text="Show and Hide Widgets").grid(row=1,column=1)
        # Button to show or hide console
        self.console_shown_text = StringVar()
        self.console_shown = True
        self._toggle_console()
        Button(self.frame,textvariable=self.console_shown_text,command=self._toggle_console).grid(row=2,column=1,sticky='nesw')
        # Button to show or hide serial interface
        self.serial_shown_text = StringVar()
        self.serial_shown_text.set("Hide all Serial controls")
        self.serial_shown = True
        Button(self.frame,textvariable=self.serial_shown_text,command=self._toggle_serial_shown).grid(row=3,column=1,sticky='nesw')
        # General help button
        Button(self.frame, text="Open Help Website", command=self._documentation).grid(row=4,column=1,sticky='nesw')
        # Automation help button
        Button(self.frame, text="Print Automation Help to Console", command = self._print_automation_help).grid(row=5,column=1,sticky='nesw')


    def get_frame(self):
        """Get the tkinter frame on which this object is drawn.
        
        :return: The widget's tkinter frame
        :rtype: tkinter.Frame
        """
        return self.frame

    def _toggle_console(self):
        """On a PC, toggles whether the console is visible; on a Mac, opens a message box with instructions to open a console manually."""
        if self.console_shown:
            try: # The code below doesn't work on macs.
                ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(),0)
            except:
                pass
            self.console_shown_text.set("Show Console")
            self.console_shown = False
        else:
            try: # The code below doesn't work on macs.
                ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(),4)
            except:
                messagebox.showinfo("Can't Open Console", "Toggling the console isn't supported on this operating system. You'll need to run this script using a launcher that generates a console, e.g. (on a Mac) IDLE or the Python Launcher with the console option selected in preferences.")
                return
            self.console_shown_text.set("Hide Console")
            self.console_shown = True

    def _toggle_serial_shown(self):
        """Toggles whether the serial port dropdowns and serial statuses are visible on all widgets that have them."""
        if self.serial_shown:
            print("Hiding serial connection widgets.")
            self.serial_shown_text.set("Show all serial controls")
            self.serial_shown = False
            for obj in self.parent.all_widgets:
                obj.hide_serial()
        else:
            print("Showing serial connection widgets.")
            self.serial_shown_text.set("Hide all serial controls")
            self.serial_shown = True
            for obj in self.parent.all_widgets:
                obj.show_serial()

    # Help/documentation functions
    def _documentation(self):
        """Open a more comprehensive document/site for support using this package."""
        webbrowser.open('https://pyopticon.readthedocs.io/')


    def _print_automation_help(self):
        """Print a crash course in the syntax for automation scripts, as well as a list of widgets' nicknames and automatable fields."""
        print("")
        print("Automation help:")
        print("The following are standalone functions that can be called in an automation script, which should be its own .py file:")
        print("- schedule_delay( delay='h:mm:ss' )")
        print("- schedule_action( target_widget_nickname, target_field_name, new_field_value, confirm=True )")
        print("- schedule_function( function )")
        print("In schedule_action, on confirm=True the widget's confirm button is pressed after updating the field.")
        print("Examples:")
        print(" schedule_delay('0:00:10')")
        print(" schedule_action( 'Argon MFC', 'Setpoint', '100', True)")
        print("In schedule_function, you may pass a function that takes no arguments, or one that takes the dashboard object as an argument, e.g.:")
        print(" schedule_function(lambda: print('Test'))")
        print(" schedule_function(lambda dashboard: print(dashboard.widgets_by_nickname['Temp'].get_field('Temperature')))")
        print("")
        print("The following are the nicknames of all available devices to control and their associated attributes you can write to:")
        for key in self.parent.widgets_by_nickname.keys():
            all_attr = ""
            for a in self.parent.widgets_by_nickname[key].attributes.keys():
                all_attr += a
                all_attr += ", "
            all_attr = all_attr[:-2]
            print("Nickname: "+key+" -- Attributes: "+all_attr+"")
        print("End automation help.")
        print("")
              
