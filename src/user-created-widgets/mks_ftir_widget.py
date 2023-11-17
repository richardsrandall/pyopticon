import numpy as np
import tkinter

from pyopticon import generic_widget

class MKSFTIRWidget(generic_widget.GenericWidget):
    """ A widget representing an MKS multi-gas 2000 FTIR.

    This widget doesn't communicate with the FTIR via serial. The FTIR is controlled by MKS software, which logs data to
    a .prn (tab-delimited) file. This widget watches one of those files and reads the gas concentrations in the last line in the file.

    One can make this widget extract several gases' data from the logfile. The gases' names are passed as one argument. 
    A .prn contains many columns, so you pass the respective column indices as another argument.
    
    You can pass in a list of calibration functions for the respective gases to adjust the FTIR's raw readings. 
    It probably makes sense to define the calibration functions using Numpy's interp function to interpolate between a range of 
    calibration points, e.g. 'ch4_cal_function_lo = lambda x: np.interp(x,[0,514,1024,1430],[0,20,40,60])'.
    
    :param parent_dashboard: The dashboard object to which this device will be added
    :type parent_dashboard: pyopticon.dashboard.PyOpticonDashboard
    :param name: The name that the widget will be labeled with, and under which its data will be logged, e.g. "Methane Mass Flow Controller"
    :type name: str
    :param nickname: A shortened nickname that can be used to identify the widget in automation scripts, e.g. "CH4 MFC"
    :type nickname: str
    :param gas_labels: The labels of the different gases to be logged. You may want to include units, e.g. 'CO2 (ppm)'
    :type gas_labels: list
    :param gas_columns: The indices of the columns corresponding to the gases' concentrations in the logfile
    :type gas_columns: list
    :param calibration_functions: A list specifying calibration functions for each gas; see the description above. If None, just keeps the values in the file.
    :type calibration_functions: list
    :param default_logfile_path: The default path of the FTIR logfile. Can be used to avoid clicking through the file location choosing dialog every time.
    :type default_logfile_path: str, optional
    """

    def __init__(self,parent_dashboard,name,nickname,gas_labels,gas_columns,calibration_functions=None,default_logfile_path=None):
        """ Constructor for a GC FID widget."""
        # Initialize the superclass with most of the widget functionality
        super().__init__(parent_dashboard,name,nickname,'#40E0D0',no_serial=True,update_every_n_cycles=3)
        # Store the fields
        self.gas_labels=gas_labels
        self.gas_columns=gas_columns
        if calibration_functions is not None:
            self.calibration_functions=calibration_functions
        else:
            f = lambda v: v
            self.calibration_functions=list(f for x in gas_labels)
        # Add the readout for the logfile location
        if default_logfile_path is None:
            def_val = "(None)"
            self.path = None
        else:
            self.path = default_logfile_path
            chunks = str.split(default_logfile_path,'/')
            def_val = chunks[len(chunks)-1]
        self.to_display=def_val
        self.add_field(field_type='text output',name="GC Logfile",label='GC logfile: ',
                       default_value=def_val,log=False)
        # Add readout fields for every gas
        for l in self.gas_labels:
            self.add_field(field_type='text output', name=l,label=l+": ", default_value='No Reading')
        # Add a button to specify the logfile location to watch
        self.button=tkinter.Button(self.get_frame(), text="Select FTIR Logfile", command=self._update_file_to_watch)
        self.button.grid(row=1,column=2)


    def on_serial_open(self,success):
        """If the device initialized successfully, do nothing; if not, set its readout to 'No Reading'

        :param success: Whether serial opened successfully, according to the return from the on_serial_read method.
        :type success: bool or str"""
        if success is not True:
            for l in self.gas_labels:
                self.set_field(l,'No Reading')
        else:
            pass

    def on_serial_query(self):
        """"Nothing is sent anywhere on a serial query for this device."""
        self.button["state"] = "disabled"#Don't want to open file dialog while serial is polling
        # Putting it here rather than on_serial_open makes it happen right when the 'connect serial' button is pressed

    def on_serial_read(self):
        """Polls the GC logfile and updates the readout with the latest values.

        :return: True if the device updated itself successfully, an error string otherwise.
        :rtype: bool or str"""
        try:
            # Open the file and grab the last line
            file = open(self.path,'r')
            lines = file.readlines()
            file.close()
            line=(lines[len(lines)-1])

            # Extract the entries that we want
            chunks = line.split('\t')
            for label, index, calibrator in zip(self.gas_labels,self.gas_columns,self.calibration_functions):
                value = float(chunks[index])
                value = calibrator(value)
                value = round(value,3)
                self.set_field(label,value)

        except Exception as e:
            #print(e)
            if self.get_field('GC Logfile')!='(None)':
                for l in self.gas_labels:
                    self.set_field(l,'Read Error')
            #return 'Failed to open and parse GC logfile.'
            # Commenting this out allows for starting logging before the GC has finished its first program cycle, 
            # though only in the default logfile location.
        return True

    def on_serial_close(self):
        """When serial is closed, set all readouts to 'No Reading'."""
        self.button["state"] = "normal"
        for l in self.gas_labels:
            self.set_field(l,'No Reading')
        self.set_field('GC Logfile',self.to_display)

    def _update_file_to_watch(self):
        """Prompt the user to select a new file to watch."""
        try:
            path = tkinter.filedialog.askopenfilename()
            self.path=path
            chunks = str.split(path,'/')
            self.to_display = chunks[len(chunks)-1]
            self.set_field('GC Logfile',self.to_display)
        except Exception as e:
            pass #Probably user x'd out file dialog
        

    def construct_serial_emulator(self):
        """No serial emulator is needed for this device, since its normal operation doesn't assume any hardware is present. Returns None.
        
        :return: None
        :rtype: NoneType
        """
        return None


    
