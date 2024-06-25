from tkinter import *
from tkinter import filedialog as fd
from tkinter import messagebox
import datetime
import os

# data logging widget
class DataLoggingWidget():
    """ This widget allows a user to choose a data logging location and to start and stop data logging

    :param parent: The dashboard to which this widget will be added.
    :type parent: pyopticon.dashboard.Dashboard
    """

    def __init__(self, parent_dashboard):
        """The constructor for a DataLoggingWidget"""
        # Parent is the labGUI object, root is the tkinter root object
        self.parent = parent_dashboard
        self.root = parent_dashboard.get_tkinter_object()
        self.main_color = '#FF7F7F'
        # Widget for data logging
        self.frame = Frame(self.root,highlightbackground=self.main_color, highlightcolor=self.main_color, highlightthickness=5)
        Label(self.frame,text="Data Logging Control").grid(row=1,column=1,sticky='nesw')
        # Select destination
        self.filename='None'
        Label(self.frame, text="Destination: ").grid(row=2,column=1,sticky='nesw')
        self.destination = StringVar()
        self.destination.set("None selected.")
        Label(self.frame, textvariable=self.destination).grid(row=2,column=2,sticky='nesw')
        self.choose_destination_button = Button(self.frame,text="(Select)", command=self._choose_destination)
        self.choose_destination_button.grid(row=2,column=3,sticky='nesw')
        # Time interval
        Label(self.frame, text="Time interval: ").grid(row=3,column=1,sticky='nesw')
        self.time_interval = StringVar()
        self.time_interval.set("0:00:10")
        self.logging_rate_entry = Entry(self.frame, textvariable=self.time_interval,width=8)
        self.logging_rate_entry.grid(row=3,column=2,sticky='nesw')
        # Start and stop logging
        self.logging_status_text = StringVar()
        self.logging_status_text.set("Start Logging")
        self.logging_active = False
        self.logging_interlock = False
        Button(self.frame,textvariable=self.logging_status_text,command = self._toggle_logging).grid(row=3,column=3,sticky='nesw')
        
        # Remember the headers and whether they've been written yet
        self.empty_file = True
        self.widgets_in_order = None
        self.widget_attributes_in_order = None

    def get_frame(self):
        """Get the tkinter frame on which this object is drawn.
        
        :return: The widget's tkinter frame
        :rtype: tkinter.Frame
        """
        return self.frame

    # Methods to support serial communication and show/hide functionality            
    def _toggle_logging(self):
        """Toggle whether data logging is active. Do the actual logging at regular intervals. Enable/disable buttons accordingly. 
        Some machinery to manage the corner case where you stop logging and then restart logging within a shorter timespan than the data logging interval."""
        if self.logging_active:
            self.logging_status_text.set("Start Logging")
            print("Stopped data logging.")
            self.logging_active = False
            self.choose_destination_button.configure(state='normal')
            self.logging_rate_entry.configure(state='normal')
            self.frame.configure(highlightbackground=self.main_color, highlightcolor=self.main_color)
            self.logging_interlock = True # This prevents one particular bug with slow polling rates
            self.root.after(self.delay*1000, self._flip_interlock) # Kludgy, sorry
            self.open_file.close()
        else:
            # Check that the time interval and filename are valid
            if self.destination.get()=="None selected.":
                messagebox.showinfo("","Please select a destination file/address.")
                return
            try:
                delay = self.logging_rate_entry.get()
                h,m,s = delay.split(":") # Delay is expected as a string in 0:00:00 format.
                self.delay = 3600*int(h)+60*int(m)+int(s)
            except:
                messagebox.showinfo("","The time interval you enter must be in 0:00:00 format.")
                return
            # Open the file
            self.mode = 'CSV'
            self.open_file = open(self.filename,'a') # Better to just avoid overwriting...
            # Do cosmetic stuff
            self.logging_status_text.set("Stop Logging")
            self.frame.configure(highlightbackground='green', highlightcolor='green')
            print("Started data logging every "+str(self.delay)+" seconds.")
            self.logging_active = True
            self.choose_destination_button.configure(state='disabled')
            self.logging_rate_entry.configure(state='disabled')
            if not self.logging_interlock: # If logging_interlock, an old request from before you hit pause is still active
                self._poll_loggable_data()
            else:
                print("You hit pause on logging recently and a an old logging callback is still pending; the logging interval will update and logging will continue when that callback executes.")

    def _flip_interlock(self):
        """Necessary for toggle_logging to handle a corner case when logging is flipped on and off in quick succession."""
        self.logging_interlock = False

    def _poll_loggable_data(self):
        """Prompt every widget to return all of the data that it wants logged. Format that data into .csv append it to the log file."""
        if not self.logging_active:
            return
        self.root.after(self.delay*1000, self._poll_loggable_data)
        all_data = dict()
        for obj in self.parent.all_widgets:
            if hasattr(obj,'log_data'):
                out = obj.log_data()
                all_data[obj.nickname] = out
        datestamp = datetime.datetime.now().strftime("%m/%d/%Y")
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        #print("Logged data at "+timestamp+".")
        
        # Create the CSV headers, if needed
        if self.empty_file or self.widgets_in_order is None:
            self.widgets_in_order = []
            self.widget_attributes_in_order = dict()
            new_header = "Date,Timestamp"
            for widget in self.parent.all_widgets:
                if not hasattr(widget,'log_data'):
                    continue
                self.widgets_in_order.append(widget)
                self.widget_attributes_in_order[widget.name]=all_data[widget.nickname].keys()
                for label in self.widget_attributes_in_order[widget.name]:
                    label = widget.nickname+": "+label
                    label = label.replace(","," -")
                    new_header+=","
                    new_header+=label
            new_header+="\n"
            if self.empty_file:
                self.open_file.write(new_header)
                self.empty_file = False
        # Create a new line and append it to the log file.
        new_line = datestamp+","+timestamp
        for widget in self.widgets_in_order:
            for attribute in self.widget_attributes_in_order[widget.name]:
                all_data[widget.nickname][attribute] = all_data[widget.nickname][attribute].replace(","," -")
                new_line+=","
                new_line+=str(all_data[widget.nickname][attribute])
        new_line+="\n"
        #self.open_file.close()
        #self.open_file = open(self.filename,'a')
        self.open_file.write(new_line)
        self.open_file.flush()

    def _choose_destination(self):
        """Open a dialog window to let the user select where the logfile should be saved."""
        datestamp = datetime.datetime.now().strftime("%m-%d-%y")
        timestamp = datetime.datetime.now().strftime('%H-%M')
        default = datestamp+"_"+timestamp+"_logfile"
        de = '.csv'
        self.filename = fd.asksaveasfilename(defaultextension=de,initialfile=default)
        f = str.split(self.filename,'/')
        f = f[len(f)-1]
        self.destination.set(f) # Just the file name, not the whole path
        if os.path.isfile(self.filename):
            # File exists already
            self.empty_file = False
        else:
            self.empty_file = True
