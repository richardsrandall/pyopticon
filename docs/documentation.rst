Documentation
=============

The ''PyOpticonDashboard'' class
**********************************
.. autoclass:: pyopticon.dashboard.PyOpticonDashboard
    :members:
    :private-members:

Superclasses for creating new widgets
**************************************

Most widgets should be created using the GenericWidget superclass, but we include the MinimalWidget class for the edge case of widgets that are purely cosmetic and don't reflect physical instruments (e.g., the built-in ''TitleWidget'' class).


The ''GenericWidget'' class
---------------------------
.. autoclass:: pyopticon.generic_widget.GenericWidget
    :members:
    :private-members:

The ''GenericSerialEmulator'' class
-----------------------------------
.. autoclass:: pyopticon.generic_serial_emulator.GenericSerialEmulator
    :members:
    :private-members:

The ''MinimalWidget'' class
---------------------------
.. autoclass:: pyopticon.minimal_widget.MinimalWidget
    :members:
    :private-members:

The ''utilities'' package
************************************

The ''scan_serial_ports'' function
-----------------------------------
.. autofunction:: pyopticon.utilities.scan_serial_ports

The ''GmailHelper'' class
-----------------------------------
.. autoclass:: pyopticon.utilities.gmail_helper.GmailHelper
    :members:
    :private-members:

Internal PyOpticon widget classes
************************************

These widgets are initialized once per dashboard by the dashboard's constructor. They control and manage all of the dashboard's high-level functions.

The ''SerialWidget'' class
-----------------------------
.. autoclass:: pyopticon._system._serial_widget.SerialWidget
    :members:
    :private-members:

The ''ShowHideWidget'' class
-----------------------------
.. autoclass:: pyopticon._system._show_hide_widget.ShowHideWidget
    :members:
    :private-members:

The ''DataLoggingWidget'' class
-----------------------------
.. autoclass:: pyopticon._system._data_logging_widget.DataLoggingWidget
    :members:
    :private-members:

The ''AutomationWidget'' class
-----------------------------
.. autoclass:: pyopticon._system._automation_widget.AutomationWidget
    :members:
    :private-members:

The ''built_in_widgets'' package
************************************

The ''TitleWidget'' class
-----------------------------
.. autoclass:: pyopticon.built_in_widgets.title_widget.TitleWidget
    :members:
    :private-members:
    :show-inheritance:

The ''SpicinessWidget'' class
-----------------------------
.. autoclass:: pyopticon.built_in_widgets.spiciness_widget.SpicinessWidget
    :members:
    :private-members:
    :show-inheritance:

The ''majumdar_lab_widgets'' package
************************************

These widgets were developed for the devices present in Prof. Arun Majumdar's lab at Stanford University.

The ''AalborgDPCWidget'' class
--------------------------------
.. autoclass:: pyopticon.majumdar_lab_widgets.aalborg_dpc_widget.AalborgDPCWidget
    :members:
    :private-members:
    :show-inheritance:

The ''MksMFCWidget'' class
--------------------------------
.. autoclass:: pyopticon.majumdar_lab_widgets.mks_mfc_widget.MksMFCWidget
    :members:
    :private-members:
    :show-inheritance:

The ''IotRelayWidget'' class
--------------------------------
.. autoclass:: pyopticon.majumdar_lab_widgets.iot_relay_widget.IotRelayWidget
    :members:
    :private-members:
    :show-inheritance:

The ''OmegaUSBUTCWidget'' class
--------------------------------
.. autoclass:: pyopticon.majumdar_lab_widgets.omega_usb_utc_widget.OmegaUSBUTCWidget
    :members:
    :private-members:
    :show-inheritance:

The ''PicarroCRDWidget'' class
--------------------------------
.. autoclass:: pyopticon.majumdar_lab_widgets.picarro_crd_widget.PicarroCRDWidget
    :members:
    :private-members:
    :show-inheritance:

The ''Valco2WayValveWidget'' class
----------------------------------
.. autoclass:: pyopticon.majumdar_lab_widgets.valco_2_way_valve_widget.Valco2WayValveWidget
    :members:
    :private-members:
    :show-inheritance:

The ''Valco8WayValveWidget'' class
----------------------------------
.. autoclass:: pyopticon.majumdar_lab_widgets.valco_8_way_valve_widget.Valco8WayValveWidget
    :members:
    :private-members:
    :show-inheritance:

The ''SRIGasChromatographFIDWidget'' class
-----------------------------------------------
.. autoclass:: pyopticon.majumdar_lab_widgets.sri_gc_fid_widget.SRIGasChromatographFIDWidget
    :members:
    :private-members:
    :show-inheritance:

The ''CellkraftHumidifierWidget'' class
-----------------------------------------------
.. autoclass:: pyopticon.majumdar_lab_widgets.cellkraft_humidifier_widget.CellkraftHumidifierWidget
    :members:
    :private-members:
    :show-inheritance:

The ''run_demo_dashboard'' function
************************************

.. autofunction:: pyopticon.demo_dashboard.run_demo_dashboard