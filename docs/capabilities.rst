Capabilities
========================

A PyOpticon dashboard consists of multiple widgets, most of which represent a physical device. 
Using a dashboard, a user can easily monitor and control multiple devices' states, providing a single 
control panel for a multi-instrument experimental setup. Our goal is to enable graduate students and 
other researchers with basic Python knowledge to quickly equip experimental setups with data acquisition and 
automated control, allowing higher-quality and higher-throughput experimentation. Here, again, is a cartoon 
of the type of system we'd like to facilitate building: 

.. image:: img/usage_cartoon.png
    :alt: A cartoon of a computer, connected to severa serial devices, displaying our application.

These are the software's core features:

* Many physical devices' states can be polled and reported to a single interface every second (or some other interval). 
  The dashboard can communicate with devices via various protocols and packages.
* The states of all those devices can be logged 
  to a .csv file suitable for analysis in Python, Matlab, 
  Excel, or other tools. 
* Widgets can also be controlled automatically according to an automation script. 
  Automation scripts are written in Python as standalone .py files using Python control structures and a simple set of functions.
* It is possible to define software interlocks that return the system to 
  a safe state, notify the user via email or text, 
  or otherwise respond when unsafe or undesireable conditions are detected. 
* It is fairly easy to create scripts that live-plot the contents of a PyOpticon logfile as the logfile is updated, 
  helping to visualize an experiment's progress.

Currently, PyOpticon comes with widgets for the following devices:

* Aalborg DPC mass flow controllers
* MKS Mass Flo Controllers, controlled by an MKS 946 Vacuum System Controller
* Picarro G2210-i Cavity Ringdown Spectrometer for CH4, CO2, H2O, and C2H6 (logging only)
* Digital Loggers IoT Relay 2, which can give on/off control of many types of AC devices
* Omega USB-UTC Thermocouple Adapters
* VICI Valco Automatic 2-Way Selector Valves
* SRI 8610C Gas Chromatographs (logging only)
* Thorlabs PM100D Optical Power Meters

We hope that PyOpticon users will write and share widgets to control their own devices, eventually creating an ecosystem 
of available widgets that others can use. 
Using the procedures outlined in the tutorial section, it is straightforward to write a new widget to control (or, if that is impractical, to simply log data from) a given physical device. 
The 'user-created-widgets' folder in the GitHub src file is where we'll place any new widgets that are sent to us.

Most widgets communicate with their device using a serial port. One can determine whether this is possible by consulting a device's manual and looking for a 
'serial,' 'RS232,' 'RS485,' or equivalent interface. While most of our devices use RS232 ASCII serial communication, PyOpticon also supports controlling devices via Modbus, 
manufacturer-provided Python drivers for specific instruments, or other Python packages for particular serial communication protocols. The Thorlabs optical power meter widget is 
a good example of a widget built around an OEM's Python driver. Each device is given its own 
thread, so devices or packages that take a while to respond (and block while they wait) are not necessarily an issue.

One can also write a widget that watches a specific computer file for updates, then 
displays those values in a widget. This is useful for devices like gas chromatographs that are far too complicated to control entirely via a user-written serial protocol, but that log 
data to a specific file, and whose data it would be convenient to log along with the data from all the dashboard-controlled instruments. See the Tutorial subsection on the GenericWidget class.

PyOpticon is also well-suited to making GUIs to control Arduino devices, as in the IoTRelayWidget in the majumdar_lab_widgets package. 
It also works quite well with LabJacks or other similar hardware to read and generate analog signals. 
It would also be quite easy to write widgets to control DC or stepper motors, using any of a number of commercially available USB-controlled H-bridge or stepper motor driver circuits. 

Note that PyOpticon was designed to sample only once per second. It might be able to sample a little faster, but not a lot faster. 
If you need more than 5 Hz sampling, you should probably look into other data acquisition and control schemes. A workaround for 
data acquisition might be a device that 'buffers' between the sensor and PyOpticon, aggregating many data points and then sending 
them all to PyOpticon when it queries once per second.
