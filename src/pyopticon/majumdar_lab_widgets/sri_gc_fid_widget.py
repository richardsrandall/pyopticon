import numpy as np
import tkinter

from .. import generic_widget

class SRIGasChromatographFIDWidget(generic_widget.GenericWidget):
    """ A widget representing an SRI gas chromatograph's flame ionization detector (FID). We use an SRI 8610c GC.

    This widget doesn't communicate with the GC via serial. The GC should be controlled using SRI's PeakSimple application. 
    PeakSimple can be programmed to log GC FID data to a '.res' file, with a row appended to the file every time a new GC 
    scan is completed. This widget watches that file and displays the results. The benefit is that the GC data then ends up 
    in the same RichardView file as all the MFC and other data, simplifying postprocessing.

    One can make this widget extract several gases' data from the logfile. The gases' names are passed as one argument. 
    A .res files contains a bunch of columns of data, so you pass this constructor the indices of the columns that correspond to 
    the peak areas for those gases.
    
    The logfile just contains peak areas, but you can pass in calibration functions that map peak areas to concentrations according 
    to some calibration curve. Since the GC FID has different sensitivity settings (low, medium, and high), you can pass 
    a set of calibration functions for each, and select which to use with a dropdown. The calibration functions are passed using 
    a dict whose keys are the labels (probably a subset of 'Low','Medium',and 'High') and whose values are a tuple of calibration 
    functions for the respective gases. For example, {'Low':(ch4_cal_function_lo,co2_cal_function_lo), 'Medium':(ch4_cal_function_med,co2_cal_function_med)}. 
    It probably makes sense to define the calibration functions using Numpy's interp function to interpolate between a range of 
    calibration points, e.g. 'ch4_cal_function_lo = lambda x: np.interp(x,[0,514,1024,1430],[0,20,40,60])'.
    
    :param parent_dashboard: The dashboard object to which this device will be added
    :type parent_dashboard: richardview.dashboard.RichardViewDashboard
    :param name: The name that the widget will be labeled with, and under which its data will be logged, e.g. "Methane Mass Flow Controller"
    :type name: str
    :param nickname: A shortened nickname that can be used to identify the widget in automation scripts, e.g. "CH4 MFC"
    :type nickname: str
    :param gas_labels: The labels of the different gases to be logged. You may want to include units, e.g. 'CO2 (ppm)'
    :type gas_labels: list
    :param gas_columns: The indices of the columns corresponding to the gases' respective peak areas in the GC FID logfile format
    :type gas_columns: list
    :param calibration_functions: A dict specifying calibration functions for each gas at one or more sensitivity settings; see the description above.
    :type calibration_functions: dict
    :param default_logfile_path: The default path of the GC FID logfile. Can be used to avoid clicking through the file location choosing dialog every time.
    :type default_logfile_path: str, optional
    """

    def __init__(self,parent_dashboard,name,nickname,gas_labels,gas_columns,calibration_functions,default_logfile_path=None):
        """ Constructor for a GC FID widget."""
        # Initialize the superclass with most of the widget functionality
        super().__init__(parent_dashboard,name,nickname,'#BF0A30',use_serial=False,update_every_n_cycles=3)
        # Store the fields
        self.gas_labels=gas_labels
        self.gas_columns=gas_columns
        self.calibration_functions=calibration_functions
        # Add the readout for the logfile location
        if default_logfile_path is None:
            def_val = "(None Chosen)"
            self.path = None
        else:
            self.path = default_logfile_path
            chunks = str.split(default_logfile_path,'/')
            def_val = chunks[len(chunks)-1]
        self.to_display=def_val
        self.add_field(field_type='text output',name="GC Logfile",label='GC logfile: ',
                       default_value=def_val,log=False)
        # Add a selector for the calibrations
        opts = list(self.calibration_functions.keys())
        self.add_field(field_type='dropdown',name='Sensitivity',label='FID Sensitivity: ',
                       default_value=opts[0],options=opts,log=True)
        self.confirm_button.grid_remove()
        # Add readout fields for every gas
        for l in self.gas_labels:
            self.add_field(field_type='text output', name=l,label=l+": ", default_value='No Reading')
        # Add a button to specify the logfile location to watch
        self.button=tkinter.Button(self.get_frame(), text="Select GC FID Logfile", command=self._update_file_to_watch)
        self.button.grid(row=1,column=2)


    def on_serial_open(self,success):
        """If the device initialized unsuccessfully, set its readout to 'No Reading'
        """
        for l in self.gas_labels:
            self.set_field(l,'No Reading',hush_warning=True)

    def disable_button(self):
        """Disable the file dialog button."""
        self.button["state"] = "disabled"#Don't want to open file dialog while serial is polling

    def on_handshake(self):
        """"On handshake, disable the file chooser button and run an update."""
        self.do_threadsafe(self.disable_button)
        self.disable_field("Sensitivity")
        self.on_update()

    def on_update(self):
        """Poll the GC logfile and updates the readout with the latest values.
        """
        try:
            # Open the file and grab the last line
            file = open(self.path,'r')
            lines = file.readlines()
            file.close()
            line=(lines[len(lines)-1])

            if not self.parent_dashboard.serial_connected:
                return

            # Extract the entries that we want
            chunks = line.split()
            cals=self.calibration_functions[self.get_field('Sensitivity')]
            for label, index, calibrator in zip(self.gas_labels,self.gas_columns,cals):
                value = float(chunks[index])
                value = calibrator(value)
                value = round(value,1)
                self.set_field(label,value)

        except Exception as e:
            #print(e)
            if self.get_field('GC Logfile')!='(None Chosen)':
                for l in self.gas_labels:
                    self.set_field(l,'Read Error')
            #return 'Failed to open and parse GC logfile.'
            # Commenting this out allows for starting logging before the GC has finished its first program cycle, 
            # though only in the default logfile location.
        return True

    def on_serial_close(self):
        """When serial is closed, set all readouts to 'No Reading'."""
        self.button["state"] = "normal"
        self.enable_field("Sensitivity")
        for l in self.gas_labels:
            self.set_field(l,'No Reading',hush_warning=True)
        self.set_field('GC Logfile',self.to_display,hush_warning=True)

    def _update_file_to_watch(self):
        """Prompt the user to select a new file to watch."""
        try:
            path = tkinter.filedialog.askopenfilename()
            self.path=path
            chunks = str.split(path,'/')
            self.to_display = chunks[len(chunks)-1]
            self.set_field('GC Logfile',self.to_display,hush_warning=True)
        except Exception as e:
            pass #Probably user x'd out file dialog
        


    
