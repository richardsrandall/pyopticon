
Tutorial: Writing Your Own Widgets
==================================

Writing your own widgets is the most complex thing you're likely to do in PyOpticon. We've tried to 
make it relatively straightforward. It's worth it, since once you're not bound to the library of existing 
widgets, you'll be free to build dashboards to control all kinds of existing and newly-acquired devices in 
your own lab or workspace. 

Extending the GenericWidget Class
**********************************

Basics
''''''''

The ``GenericWidget`` class is meant to allow widget development with less tedium and with less knowledge of tkinter, 
Pyserial, and other specialized libraries. This is done by defining a superclass (``GenericWidget``) from which subclasses 
(e.g., ``Valco2WayValveWidget``) are defined. If you haven't worked much with object-oriented programming before, it's 
probably worth reading a primer elsewhere (like this_) on classes, objects, and inheritance. In short, the code that all 
widgets share is written in a superclass, and when writing a subclass you need only write the code that is unique to the 
widget that you're trying to create. 

.. _this: https://realpython.com/python3-object-oriented-programming/#how-do-you-define-a-class-in-python 

We recommend using ``GenericWidget`` as the superclass for all widgets representing physical devices, and in fact for 
all widgets except for purely cosmetic ones. 
A later section talks about ``MinimalWidget``, which lets you build widgets completely from scratch, which 
we only recommend if you're making a purely cosmetic widget like a ``TitleWidget``, or if you need really special 
behavior and you really know what you're doing.

We'll run through an example of building the Valco 2 Way Valve widget from the ``majumdar_lab_widgets`` package. This is a 
convenient example because it's only got one output field (the valve's actual position) and one user input field (the desired 
valve position). An important first step is to know this device's serial communication protocol. We'll assume we know the protocol 
for the valve already, but if we didn't, the next section includes tips on how to find it.

The properties of ``GenericWidget`` subclasses are mostly stored as what PyOpticon refers to as 'fields'. A field is a 
text variable with a text identifier, a corresponding graphical element, and a label. For example, in the 
``Valco2WayValveWidget`` class, there's a field for 'Position Selection' corresponding to a dropdown menu 
and there's a field for 'Actual Position' corresponding to a text readout. Fields are created using the ``add_field`` 
method, read using the ``get_field`` method, and set using the ``set_field`` method, all of which are described in the 
documentation. The point of using PyOpticon fields rather than instance variables is to let you avoid messing with 
tkinter GUI elements and StringVar objects, 
provide a clean way for automation scripts to control widgets, and let you avoid manually defining a ``log_data`` 
function for most widgets.

Now that we've described fields, here are the functions/methods that you may want to implement for most widgets:

* ``__init__``: the constructor method; required
* ``build_serial_object``: called before the first serial query; opens whatever serial connection is needed
* ``on_handshake_query``: sends a query to check that the proper device is connected to the serial line
* ``on_handshake_read``: reads the result of the handshake and returns whether or not it was valid
* ``on_serial_open``: called right after the handshake read, with an argument denoting handshake success or failure
* ``on_serial_query``: called when the dashboard prompts the widget to query its serial line for new readings
* ``on_serial_read``: called when the dashboard prompts the widget to check its serial line for a response
* ``on_serial_close``: called just after the serial connection closes
* ``on_confirm``: called when the user clicks the confirm button

All widgets should have ``__init__``, ``on_serial_open``, ``on_serial_query``, ``on_serial_read``, and ``on_serial_close`` 
implemented. All widgets that write values to the device, as opposed to just reading values, should have ``on_confirm`` 
implemented. Devices that use a serial connection other than a pySerial Serial object (i.e., simple ASCII RS232 communication) 
should override the default ``build_serial_object`` method.

Finally, the default behavior is to use ``on_serial_query`` as the 
``on_handshake_query`` method and ``on_serial_read`` as the ``on_handshake_read`` method, with the handshake considered to 
have failed if ``on_serial_read`` raises an exception. Basically, by default you can use a normal query/read cycle as a 
handshake, but you have the option of having a 'special' handshake that happens the first time only. A special handshake is handy if you want 
to query the instrument for something like a device ID that need not be queried every single cycle.

Below, we've included the whole ``Valco2WayValveWidget`` implementation; reading that is probably the easiest way to 
understand what all these methods do. But first, here are a couple of important points:

*   Generally, you don't need to worry about 1) initializing the Pyserial object, 2) handling any errors that come from 
    failing to initialize the Pyserial object, or 3) checking whether the serial connection is open before you send it a 
    command. The functions that call  ``on_serial_open``, ``on_serial_query``, ``on_serial_read``, 
    ``on_serial_close``, and ``on_confirm`` take care of these 
    things for you, so you can leave them be unless you want to override their behavior.

*   It's best to initialize most widget properties and graphical elements as PyOpticon fields. 
    Any PyOpticon fields can be read using ``get_field``, set using ``set_field``, 
    controlled in automation scripts using ``schedule_action``, and will be logged by default. If you just want 
    to store internal values that aren't logged or shown in the GUI, instance variables (e.g. ``self.some_value=19``) 
    work just fine.

*   The default behavior of ``log_data`` as defined in ``GenericWidget`` is usually fine, but you can override it if you need to 
    process the data before logging it or log data that aren't PyOpticon fields. It just needs to return a ``dict`` of the 
    names and values of the data to be logged at a given time step.

*   The ``on_handshake_read`` method is expected to return ``True`` or ``None`` if a valid response was read from 
    the serial port and to raise an exception or return ``False`` or a string error message otherwise. 
    This is important because when the widget first queries and reads from the serial device,
    the return value of ``on_handshake_read`` is passed as an argument to ``on_serial_open``. If ``on_serial_open`` receives a 
    value of ``False`` or ``'Failed to Parse Response'``, you'll probably want set the values of the sensor readouts to something like "No Reading". 
    If it returns a string error message, that message will automatically be printed to the console. By default, ``on_serial_read`` is 
    used as ``on_handshake_read``, and the handshake will be considered successful unless ``on_serial_read`` raises an exception or 
    returns ``False`` or a string error message.

*   There are a couple of special features of ``GenericWidget`` that are meant to deal with funny edge cases, like a widget with 
    no serial connection or a device that takes a long time to respond to serial queries. 
    Check out the "GenericWidget Tricks and Features" section below for a tour of some of these, or refer to the 
    "Documentation" tab.

*   Some physical devices are finnicky about receiving too many serial queries in a row, and want a delay between 
    consecutive commands. This can be addressed with the ``send_via_queue`` method described below. Also, often 
    the first polling cycle right after 'confirm' is pressed will generate a 'read error' before returning to normal. 
    That happens because the confirm button is pressed between two queries, and the device gives a serial response 
    to the command, interspersing an unexpected response between the two responses to the queries. ``send_via_queue`` can 
    also fix this by ensuring that all queries get sent before any pending commands from a confirm press are sent.

With all that in mind, here's the implementation of ``Valco2WayValve``, with some of the comments adjusted from the source code 
for clarity and brevity. We just construct a widget, add an input and output field, and define how to send and parse serial 
communications with the valve.

.. code-block:: python

    import numpy as np

    from .. import generic_widget
    from .. import generic_serial_emulator

    class Valco2WayValveWidget(generic_widget.GenericWidget):
        # Docstring has been cut out to save space.
        # Note that valve_positions is a list of the names of the valve's positions.

        def __init__(self,parent_dashboard,name,nickname,default_serial_port,valve_positions,valve_id='1'):
            """ Constructor for a VICI Valco 2-way valve widget."""
            # Initialize the superclass (GenericWidget) with most of the widget functionality
            super().__init__(parent_dashboard,name,nickname,'#ADD8E6',default_serial_port=default_serial_port,baudrate=9600)
            # Record the valve id
            self.valve_id=valve_id.encode('ascii')
            # Add a dropdown field
            self.valve_positions=valve_positions
            self.add_field(field_type='dropdown', name='Position Selection',label='Selected Position: ',
                        default_value=self.valve_positions[0], log=True, options=self.valve_positions)
            # Add a readout field
            self.add_field(field_type='text output', name='Actual Position',
                        label='Actual Position: ', default_value='No Reading', log=True)
            # Move the confirm button
            self.move_confirm_button(row=3,column=2)

        def on_serial_open(self,success):
            """If serial opened successfully, do nothing; if not, set readouts to 'No Reading'

            :param success: Whether serial opened successfully, according to the return from the on_serial_read method.
            :type success: bool
            """
            if not success:
                self.set_field('Actual Position','No Reading')

        def on_serial_query(self):
            """Send a query to the valve asking for its current position.
            """
            # Flush any old responses
            self.get_serial_object().reset_input_buffer()
            # Commands are something like b'1CP\r', where 1 is the valve ID and CP means 'current position'
            self.get_serial_object().write(self.valve_id+b'CP\r')

        def on_serial_read(self):
            """Parse the responses from the previous serial query and update the display. Return True if the response is valid and False if not.

            :return: True if all the response was of the expected format, False otherwise.
            :rtype: bool
            """
            status = str(self.serial_object.readline())
            # The response is something like b'1\A' or b'1\B', where A and B are the valve's 2 positions
            try:
                i = status.index("\"")+1
                is_A = status[i]=='A'
                if is_A:
                    self.set_field('Actual Position',self.valve_positions[0])
                else:
                    self.set_field('Actual Position',self.valve_positions[1])
            except Exception as e:
                self.set_field('Actual Position','Read Error')
                return False
            return True

        def on_serial_close(self):
            """When serial is closed, set all readouts to 'None'."""
            self.set_field('Actual Position','No Reading')

        def on_confirm(self):
            """When 'confirm' is pressed, send the appropriate commands to the valve.
            """
            # GenericWidget already checks whether serial is connected, and complains if not.
            selected = self.get_field('Position Selection')
            if not (selected in self.valve_positions):
                print("\"Confirm\" pressed with no/invalid option selected.")
                return
            choice = self.valve_positions.index(selected)
            # Command is something like b'1GOA\r' or b'1GOB\r' where A and B are the 2 valve positions
            if choice==0:
                print("Moving valve \""+self.name+"\" to \""+selected+"\" (A)")
                self.serial_object.write(self.valve_id+b'GOA\r')
            else:
                print("Moving valve \""+self.name+"\" to \""+selected+"\" (B)")
                self.serial_object.write(self.valve_id+b'GOB\r')

        def construct_serial_emulator(self):
            """Get the serial emulator to use when we're testing in offline mode.
            A later section of the tutorial explains what this means.

            :return: A valco 2-way valve serial emulator object.
            :rtype: pyopticon.majumdar_lab_widgets.valco_2_way_valve_widget.Valco2WayValveSerialEmulator"""
            return Valco2WayValveSerialEmulator()

Here's what the widget ends up looking like:

.. image:: img/valco_widget.png
    :alt: A Valco2WayValve widget


Connecting to Instruments with Text-Based Serial Protocols
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Many instruments communicate with computers by receiving and sending binary-encoded text messages. By default, PyOpticon 
widgets use this type of communication, enabled by the pySerial Python package. 

In principle, a PyOpticon widget with pySerial can control any instrument that uses a text-based serial protocol. 
In practice, finding that protocol can be tricky. The protocol consists of a baud rate (an integer value, 
like 19200), a syntax for sending commands, and a syntax in which replies are sent.

It's easiest if you can find a manual for your device that contains its serial protocol. If that fails, often the 
manufacturer will have documentation on the serial protocol that they can send upon request. It may be referred to 
as an RS232, DB9, or serial protocol.

If you have a manufacturer-supplied program that can talk to the device, you can also try to listen in on its connection 
and reverse-engineer the serial protocol. Some programs that may help do this are portmon, com0com, and realterm. This works 
best for simple devices that send the same commands over and over. Trying to reverse-engineer the protocol for a complex 
instrument in this way would be quite hard.

To connect to an instrument, find the appropriate set of cables and converters. USB-to-RS232 converters are available 
on Amazon and tend to work pretty well. We've had some issues using USB-to-many-RS232 multiplexers -- it seems a bit 
more reliable to use a USB multiplexer coupled to many USB-to-RS232 cables. You can use the serial port scanner to verify 
that a new serial port appeared when the instrument was plugged in. Sometimes, you need to change settings on the instrument 
to enable serial communications; if so, the manual may explain how to do so.

Before trying to code a PyOpticon widget, we recommend sending the relevant commands manually to make sure the protocol works as 
expected. One easy way to do this is to use the pySerial library in the Python shell, accessed via IDLE. The pySerial 
website has some useful examples_.

On occasion, an instrument will require serial parameters like parity and stop bits that are different from the pySerial default. 
Simple overide the ``build_serial_object`` function, replacing it with a function that sets ``self.serial_object`` to a pySerial 
Serial object that was constructed with whatever special parameters are required, per the online pySerial documentation.

Connecting to Instruments with Other Python Serial Packages
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

There are various other serial communication standards besides RS232 with ASCII-encoded text. One example is the 
RS485 standard with the Modbus communication protocol, a system commonly used for industrial controls. Another is 
the VISA standard, which helps manufactuers create cross-platform drivers for there instruments. There are 
existing Python libraries to facilitate communications using many of these standards, such as minimalmodbus and pyvisa. 

The workflow to use one of these protocols is similar to that for 'plain' RS232 serial. First, write a standalone (non-PyOpticon) 
Python script that can read from and write to your instrument, ensuring that you understand how Python communicates with your 
instrument. Second, overide the ``build_serial_object`` function in your widget class, replacing it with a function 
that sets ``self.serial_object`` to whatever object represents your serial connection (e.g. a ``pymodbus.ModbusSerialClient`` object). 
If ``build_serial_object`` raises an exception or returns ``None``, the connection will be assumed to have failed. Then, 
implement the handshake, query, read, and confirm methods as normal. Note that if you wish to use ``write_via_queue``, the 
serial object must have a ``write`` method. Additionally, see the note below on 'blocking code'.

The built-in CellKraft humidifier widget is a good example of a widget that uses Modbus communications instead of ASCII text-based 
serial communications.

Connecting to Instruments with Manufacturer-Provided Python Drivers
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Many instrument manufacturers already provide Python drivers to interface with their instruments. 
To use one of these drivers, just overide the ``build_serial_object`` function in 
your widget class, replacing it with a function 
that sets ``self.serial_object`` to whatever object represents the device. If ``build_serial_object`` raises an exception or 
returns ``None``, the connection will be assumed to have failed. Then, 
implement the handshake, query, read, and confirm methods as normal. Note that if you wish to use ``write_via_queue``, the 
serial object must have a ``write`` method, so it probably won't work with most 3rd-party drivers. 
See the note on blocking code below.

See the project Github-->user-created-widgets-->thorlabs_opm_widget for an example of a widget that uses a manufacturer-provided 
API to communicate to the instrument. In this case, Thorlabs provided a Python wrapper for a .dll driver that makes it very 
easy to query a light power meter.

Using Drivers and Serial Libraries with Blocking or Asynchronous Code
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
One caveat is to be careful of drivers or library with blocking code. Blocking code is code that occupies the entire program 
until it executes. With non-blocking text-based pySerial communications, you can instantaneously write to the device, 
do other things elsewhere in the program, then check back later to see if there was a response. PyOpticon uses this to 
query many devices in parallel. However, a pymodbus query will block all other tasks for ~0.1s while it waits for an instrument to respond. 
The same is true of using the Thorlabs driver to query a light meter. 

Suppose a blocking serial call takes ~0.1s to receive a response to its query. If there's only blocking code for one query in one 
widget, it's not the end of the world. However, if you have 4 widgets each of which makes 3 blocking modbus queries per 
cycle, the total blocking time would be ~1.2s, which is greater than PyOpticon's refresh period and would likely cause a crash 
or poor performance. So if you must use a blocking query to an instrument, note that it won't scale very well. Note that blocking code to initialize 
a serial object is normal and not a big deal; blocking in query-response cycles is the issue.

This is our advice for working around this problem:

#. Use a pyserial Serial object with the usual query-read structure wherever possible, or another package that allows you to query and then check later for responses.
#. If you must use blocking queries, use as few as possible in each widget refresh, use as few of those widgets as possible, and use ``update_every_n_cycles`` to make the blocking queries happen less frequently.
#. If that fails, find an asynchronous serial library to achieve the type of control you want. See below.

Asyncio is Python's built-in utility for running tasks asynchronously, which can be useful for letting serial queries take place in 
the background. Asynchronous versions often exist both for serial protocol packages (e.g. pymodbus) and for manufacters' drivers. 
PyOpticon supports the use of asyncio through the ``async-tkinter-loop`` package. 
Look at ``built_in_widgets.async_demo_widget`` for a simple example of how to use 
an asynchronous routine to update the state of a widget. While asyncio is powerful, it's a bit of an advanced Python topic, 
so PyOpticon was designed to work without it. So, getting asyncio to work perfectly with the ``generic_widget`` superclass, 
while possible, can be a bit annoying. But if you understand asyncio, you can definitely figure it out.

.. _examples: https://pyserial.readthedocs.io/en/latest/shortintro.html

GenericWidget Tricks and Features
''''''''''''''''''''''''''''''''''''''''''

In developing widgets for our own lab, there were a few things for which we added special options in the ``GenericWidget`` 
class. They're buried in the documentation, so we will quickly highlight some here:

*   Disabling fields: If you want to grey out an input field, perhaps so you can't change it while the serial connection 
    is active, the ``disable_field`` and ``enable_field`` methods will let you do that.
*   If the 'Confirm' button is autogenerated in an inconvenient place, 
    you can move it using the ``move_confirm_button`` method.
*   The ``override_color`` method lets you change the color of a widget's frame from the default for that type of widget.
*   The optional ``update_every_n_cycles`` argument to the ``GenericWidget`` constructor creates a widget that updates every 
    2nd, 3rd, or nth cycle instead of every cycle. This is useful for instruments that take a while to respond to serial queries, 
    or for widgets that have unavoidable blocking code in their read or query methods 
    that you want to call infrequently so it doesn't gum up the dashboard. If the widget updates every n cycles, 
    ``on_serial_query`` is called on the 0th cycle and ``on_serial_read`` is called halfway through the ``int(n*4/5)`` th cycle. 
    E.g., with a dashboard cycling once per second, a device that updates every 10 seconds would read 8.5 seconds after it queries, 
    and a device that updates every 3 seconds would read 2.5 seconds after it queries. The ``SpicinessWidget`` class is initalized 
    with ``update_every_n_cycles=3`` to demonstrate this option.
*   The optional ``no_serial`` creates a widget that never attempts to connect through a serial port and is lacking a serial 
    port selection dropdown or a serial status readout. You might want this for a widget that reports the contents of some 
    other program's logfile, queries an instrument through a manufacturer-provided Python API, or doesn't represent a physical 
    device at all. The ``on_serial_query`` and ``on_serial_read`` methods are still called on the normal schedule, so you can 
    put the logic to update the widget in either. The ``SpicinessWidget`` class exists to demonstrate a no-serial widget, though 
    all it does is report a random level of spice.
*   The optional ``widget_to_share_serial_with`` field allows multiple widgets to share the same serial connection. For example, 
    up to 6 MKS mass flow controllers are run by one 'control box' on one serial line, but we want each to have its own  widget. 
    We initalize the first MFC as normal, and then pass it as the ``widget_to_share_serial_with`` argument to every subsequent 
    one. In every widget but the first, the serial dropdown and readout are removed. When serial communication opens, the first 
    widget initializes its serial object as normal, and then every later widget shares the same object. The demo widget shows how 
    to initialize two MKS MFC widgets that share a serial port, and the ``MksMFCWidget`` class shows how to implement this with 
    calls to the ``GenericWidget`` constructor.
*   The ``send_via_queue`` method lets you add a serial write to a queue of pending serial writes. It will be sent a 
    specified delay in milliseconds after the previous command in the queue being sent (or,that many milliseconds 
    after it was added to the queue, if the queue was empty to start). This lets you ensure that commands get sent in a 
    certain order and that there's always a certain spacing between commands without needing to use tkinter's ``after`` method. 
    Note that it doesn't work super well with widgets that share serial with other widgets; the order in which things get 
    sent from the queue can get scrambled.

Using Serial Emulators for Offline Testing
**********************************************

Often, it's nice to be able to develop widgets a dashboard without access to the physical devices. It's nice to be 
able to assemble a dashboard or code all the graphical elements of a widget at home on a laptop, and only do the final 
debugging in the lab on the lab computer. To this end, we've created "Serial Emulators" that imitate a serial connection 
to a real instrument, letting you operate a dashboard full of fake instruments instead.

To run a dashboard in offline mode, using serial emulators where they're available, simply pass the option 
``use_serial_emulators=True`` to the dashboard's constructor. This is the default for the demo dashboard.

When you're writing a widget class, we highly recommend that you create at least a simple serial emulator. A serial 
emulator implements some of the methods of a Pyserial Serial object, and therefore 
looks like a Pyserial Serial object to a dashboard or widget. The possible methods to implement are:

* ``__init__``
* ``write``
* ``readline``
* ``readlines``
* ``flush_input_buffer``
* ``close``

See the documentation for details. Note that serial objects usually take and return ascii-encoded binary strings, 
which are written in Python as ``b'text'`` or ``"text".encode('ascii')``. Not all methods need to be implemented - for 
a simple device that only queries and reads a single value, you can get by with only implementing ``readline``. 
You can make an emulator very simple, returning hard-coded or random measurements, or complex, changing the state of 
the imaginary device in response to received commands. They extend the ``GenericSerialEmulator`` class.

Here's the serial emulator object from the ``iot_relay_widget`` module:

.. code-block:: python

    class IoTRelaySerialEmulator(generic_serial_emulator.GenericSerialEmulator):
        """Serial emulator to allow offline testing of dashboards containing IoT relay widgets.
        Acts as a Pyserial Serial object for the purposes of the program, implementing a few of the same methods.
        Confirms to console when an on/off command is sent, and otherwise returns a randomly selected 'on' or 'off' status.
        """
        # This class simulates what a real instrument would respond so I can test code on my laptop
        def write(self,value):
            """Write to this object as if it were a Pyserial Serial object. Ignores queries and reports on/off commands to console."""
            if 'Q' in str(value):#Ignore queries
                return
            print("UV LED got command: "+str(value)+"; ignoring.")

        def readline(self):
            """Reads a response as if this were a Pyserial Serial object. The only time readline is called is to check the response to a status query."""
            v = np.random.randint(0,20)
            v = 'On' if v>10 else 'Off'
            v = str(v)+'\r\n'
            return v.encode('ascii')


Extending the MinimalWidget Class
**********************************

For all widgets representing physical devices, we suggest extending the ``GenericWidget`` class, which saves a lot of work 
compared to building one from scratch. Even for widgets that don't represent a physical device, e.g. some kind of 
calculator widget to help the operator, it may be easiest to just use a ``GenericWidget`` subclass with the 
``no_serial=True`` option, which can save some messing with tkinter GUI elements. However, we include the ``MinimalWidget`` 
class in case you really do want to build a widget from scratch.

The ``MinimalWidget`` class implements only the few methods that are required for a widget to interface with its parent 
dashboard (listed in the corresponding section in the Documentation tab). 
All of those methods default to doing nothing, though of course you can override them.

The most likely use of the ``MinimalWidget`` is writing a widget that is purely cosmetic. Such a widget needs none of the 
serial or logging machinery of a ``GenericWidget`` subclass, nor would it want to be stuck with a ``GenericWidget`` subclass' 
colored frame and gridded layout. A MinimalWidget class just contains a tkinter frame object on which anything can be drawn, 
e.g. text, images, etc. The only widget we've written that extends ``MinimalWidget`` is the ``TitleWidget``, whose entire 
implementation is included below: 

.. code-block:: python

    from tkinter import *
    import tkinter.font as tkFont
    from .. import minimal_widget

    class TitleWidget(minimal_widget.MinimalWidget):
        """ A simple widget containing only text, intended for making a big-text title for a dashboard. 
        Uses the MinimalWidget superclass, since all of the GenericWidget machinery is unnecessary.\n

        :param parent_dashboard: The dashboard object to which this device will be added
        :type parent_dashboard: pyopticon.dashboard.PyOpticonDashboard
        :param title: The text to be displayed within this widget, called 'title' because it's likely to be the title of the entire dashboard.
        :type title: str
        :param font_size: The size of font to be used in the text, as an integer.
        :type font_size: int
        """

        def __init__(self,parent_dashboard,title,font_size):
            """ Constructor for a title widget."""
            super().__init__(parent_dashboard)
            fontStyle = tkFont.Font(size=font_size)
            # This entire widget is just one big Label
            Label(self.frame, font = fontStyle, text = title).pack()


