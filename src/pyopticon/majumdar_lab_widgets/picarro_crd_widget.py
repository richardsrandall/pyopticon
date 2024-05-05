import numpy as np

from .. import generic_widget

class PicarroCRDWidget(generic_widget.GenericWidget):
    """ Widget for a Picarro GG201-i isotopic analyzer that measures 0-30 ppm CH4, 200-2000+ ppm CO2, and 0-100% relative humidity.\n

    Refer to the Picarro manual to configure one of its extra serial ports for data logging to an external device. Two modes are possible. 
    In one, the Picarro listens for a query and replies with its latest measurements. In the other, the Picarro sends its latest measurements every second. 
    We chose to use the 'send measurements every second' option. This means that the Picarro widget only listens for measurements, and doesn't ever send 
    any queries via the serial line. There wasn't a super strong reason for choosing one over the other, except for slightly more resilience to the 
    Picarro 'lagging' for a few seconds when it receives a methane concentration above its 30 ppm 'limit'.\n

    The Picarro needs to be set to send (in this order) the CH4 concentration in ppm, the water concentration in volume percent, and the CO2 concentration in ppm. 
    This is done using the Picarro's own monitor and interface, as described in its manual -- contact the manufacturer if your manual doesn't tell you how to do this.

    :param parent_dashboard: The dashboard object to which this device will be added
    :type parent_dashboard: richardview.dashboard.RichardViewDashboard
    :param name: The name that the widget will be labeled with, and under which its data will be logged, e.g. "Methane Mass Flow Controller"
    :type name: str
    :param nickname: A shortened nickname that can be used to identify the widget in automation scripts, e.g. "CH4 MFC"
    :type nickname: str
    :param default_serial_port: The name of the default selected serial port, e.g. 'COM9'
    :type default_serial_port: str
    """

    def __init__(self,parent_dashboard,name,nickname,default_serial_port):
        """ Constructor for a Picarro cavity ringdown spectrometer widget."""
        # Initialize the superclass with most of the widget functionality
        super().__init__(parent_dashboard,name,nickname,'#c32148',
                         default_serial_port=default_serial_port,baudrate=19200,update_every_n_cycles=3)
        # Add some readout fields
        self.add_field(field_type='text output', name='CH4 (ppm)',
                       label='CH4 (ppm): ', default_value='No Reading', log=True)
        self.add_field(field_type='text output', name='CO2 (ppm)',
                       label='CO2 (ppm): ', default_value='No Reading', log=True)
        self.add_field(field_type='text output', name='H2O (vol %)',
                       label='Water (vol %): ', default_value='No Reading', log=True)
        self.num_fails=0

    def on_failed_serial_open(self):
        """If serial opened unsuccessfully, set readouts to 'No Reading'
        """
        for field in ('CH4 (ppm)','CO2 (ppm)','H2O (vol %)'):
            self.set_field(field,'No Reading',hush_warning=True)

    def on_update(self):
        """Parse the latest message from the Picarro and update the display.\n
        Note that sometimes we get unlucky with the timing and a valid Picarro message gets chopped off halfway through and fails to parse. So occasionally we get a 'read error' 
        when the instrument is behaving just fine. This is easy to fix in data post-processing, but we might also consider fixing it by switching to a query-response setup.
        """
        if not self.parent_dashboard.serial_connected:
            return
        try:
            if not self.parent_dashboard.offline_mode:
                self.get_serial_object().readline()
                resp = str(self.get_serial_object().readline())
                self.get_serial_object().reset_input_buffer()
            else:
                s = ' < '+str(np.random.randint(2,100))+' '+str(np.random.randint(10,1000)*0.01)+' '+str(np.random.randint(400,600))+' > \r'
                resp = str(s.encode('ascii'))
            values = resp.split()
            #print(values)
            if len(values)!=7:
                raise Exception('Bad response format.')
            ch4 = str(round(float(values[2]),4))
            h2o = str(round(float(values[3]),4))
            co2 = str(round(float(values[4]),4))
            self.set_field('CH4 (ppm)',ch4)
            self.set_field('CO2 (ppm)',co2)
            self.set_field('H2O (vol %)',h2o)
            self.num_fails=0
            return True # A valid response from the Picarro was read
        except Exception as e:
            self.num_fails+=1
            if self.num_fails>3:
                for field in ('CH4 (ppm)','CO2 (ppm)','H2O (vol %)'):
                    self.set_field(field,'Read Error')
            fail_message=("Unexpected response received from Picarro CRD: "+str(resp))

    def on_serial_close(self):
        """When serial is closed, set all readouts to 'None'."""
        for field in ('CH4 (ppm)','CO2 (ppm)','H2O (vol %)'):
            self.set_field(field,'No Reading',hush_warning=True)


        

    
