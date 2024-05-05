
# Main PyOpticon imports
import pyopticon.majumdar_lab_widgets as mlw
import pyopticon.built_in_widgets as biw
from pyopticon.dashboard import PyOpticonDashboard

# Other packages
import traceback
import sys

    # Custom widgets
from custom_widgets.labjack_cl2_sensor_widget import LabJackCl2SensorWidget
from custom_widgets.flow_calc_widget import FlowCalcWidget
from custom_widgets.mks_ftir_widget import MKSFTIRWidget
from custom_widgets.aalborg_dpm_widget import AalborgDPMWidget
from custom_widgets.aalborg_dfc_widget import AalborgDFCWidget

def run_main_dashboard():
    """Run a demo dashboard, configured for offline use via serial emulators, including 
    widgets for a thermocouple, two MKS MFC's, an Aalborg MFC, an Picarro spectrometer, 
    and an ultraviolet light controlled via an IoT relay. Intended for early learning of 
    how to use a PyOpticon dashboard."""

    # How to construct a dashboard:
    # - Define all of the widgets you want
    # - Load them into your window, specifying grid positions
    # - Remember that Column 1 is reserved for system GUI elements

    # Create a dashboard object
    dashboard = PyOpticonDashboard(dashboard_name = "Methane Oxidation Reactor",
                                offline_mode=1,
                                polling_interval_ms=1000,
                                window_resizeable=False,
                                persistent_console_logfile = True,
                                x_pad=10,
                                y_pad=10,
                                print_stacktraces=False)

    # The next many sections initialize each of the individual widgets.

    # Add a title block
    dashboard.add_widget(biw.TitleWidget(dashboard,"Methane Oxidation\nReactor Controls",20),0,1)

    # Add a thorlabs power meter widget
    lm1 = mlw.ThorlabsLightMeterWidget(parent_dashboard=dashboard,
                                name='Light Power Meter',
                                nickname='Light Power Meter',
                                wavelength=365,
                                scale_factor=(1.0/0.78))
    dashboard.add_widget(lm1,row=0,column=2)

    # Add the LabJack chlorine didget
    lm1 = LabJackCl2SensorWidget(parent_dashboard=dashboard,
                                name='Chlorine Sensor LabJack',
                                nickname='Cl2 LabJack',
                                ch1_name = 'Inlet Cl2 (mV)',
                                ch1_calibration = lambda x: x*1000,
                                ch2_name = 'Outlet Cl2 (mV)',
                                ch2_calibration = lambda x: x*1000)
    dashboard.add_widget(lm1,row=0,column=3)

    # Add a thermocouple widget
    tc1 = mlw.OmegaUSBUTCWidget(parent_dashboard=dashboard,
                                name='Reactor Thermocouple',
                                nickname='Reactor TC',
                                default_serial_port='COM14')
    dashboard.add_widget(tc1,row=1,column=3)

    # Add an UV LED controller controlled with an IoT relay
    uv_led_1 = mlw.IotRelayWidget(parent_dashboard=dashboard,
                                name='UV Light',
                                nickname='UV Light',
                                default_serial_port='COM6')
    dashboard.add_widget(uv_led_1,row=2,column=3)

    # Add a gas chromatograph
    gc_1 = mlw.SRIGasChromatographFIDWidget(parent_dashboard=dashboard,
                                name='Gas Chromatograph FID',
                                nickname='GC FID',
                                gas_labels=('CH4 (ppm)','CO2 (ppm)'),
                                gas_columns=(10,15),
                                calibration_functions={'High':(lambda x: 0.2383*x, lambda x: 4.2827*x),'Medium':(lambda x: 4.6512*x, lambda x: 4.2827*x)}, 
                                default_logfile_path=None)
    dashboard.add_widget(gc_1,row=4,column=0)

    # Add an FTIR widget
    ftir1 = MKSFTIRWidget(parent_dashboard=dashboard,
                          name='MKS FTIR',
                          nickname='FTIR',
                          gas_labels=('CH4 (ppm)','CO2 (ppm)','H2O (ppm)','CO (ppm)'),
                          gas_columns=(27,30,18,9))
    dashboard.add_widget(ftir1,row=3,column=3)

    # Add a Valco 2-way valve
    #valve_1 = mlw.Valco2WayValveWidget(parent_dashboard=dashboard,
    #                                name='Reactor Bypass Valve',
    #                                nickname='Reactor Bypass Valve',
    #                                default_serial_port='COM11',
    #                                valve_positions=['Thru Reactor','Bypass Reactor'])
    #dashboard.add_widget(valve_1,row=2,column=1)

    # Add a flow rate calculator
    calc = FlowCalcWidget(parent_dashboard=dashboard,
                                name='Flow Rate Calculator',
                                nickname='Flow Calc')
    dashboard.add_widget(calc,row=4,column=1)

    # Add a Picarro Cavity Ringdown Spectrometer
    picarro_1 = mlw.PicarroCRDWidget(parent_dashboard=dashboard,
                                name='Picarro (COM 11)',
                                nickname='Picarro',
                                default_serial_port='DISABLED')
    dashboard.add_widget(picarro_1,row=4,column=3)

    # Add an Aalborg MFC
    mfc1=mlw.AalborgDPCWidget(parent_dashboard=dashboard,
                            name='Methane MFC (0-50sccm)',
                            nickname='Methane MFC',
                            default_serial_port='COM10')
                            #calibration=((0,200),(0,100)))
    dashboard.add_widget(mfc1,row=1,column=1)

    # Add an Aalborg MFC
    mfc2=mlw.AalborgDPCWidget(parent_dashboard=dashboard,
                            name='Low-Flow N2/Ar/air MFC (0-50sccm)',
                            nickname='LF N2 MFC',
                            default_serial_port='COM9')
                            #calibration=((0,200),(0,100)))
    dashboard.add_widget(mfc2,row=1,column=2)

    # Add an Aalborg MFC
    mfc3=mlw.AalborgDPCWidget(parent_dashboard=dashboard,
                            name='Oxygen MFC (0-50sccm)',
                            nickname='O2 MFC',
                            default_serial_port='COM16')
                            #calibration=((0,200),(0,100)))
    dashboard.add_widget(mfc3,row=2,column=1)

    # Add an MKS MFC
    mfc4=mlw.MksMFCWidget(parent_dashboard=dashboard,
                        name='High-Flow N2/Ar/air MFC (0-500sccm)',
                        nickname='HF N2 MFC',
                        device_id='253',
                        channel='A1',
                        default_serial_port='COM8',
                        force_scale_factor=0.34,
                        #calibration=((0,25,50,100,150,200,250,300,350),(0,24.9,52.4,107,161.3,215.2,269.2,323.3,377.3))) # 10/31/23
                        calibration=((0,350),(0,350))) # 2/28/24 Removing calibration curve and just using scale factor
    dashboard.add_widget(mfc4,row=2,column=2)

    # Add an Aalborg MFC
    mfc4=mlw.AalborgDPCWidget(parent_dashboard=dashboard,
                            name='Humid N2/Ar/Air MFC (0-500sccm)',
                            nickname='Humid N2 MFC',
                            default_serial_port='COM19')
                            #calibration=((0,200),(0,100)))
    dashboard.add_widget(mfc4,row=3,column=1)

    # Add an Aalborg MFM
    mfm1=AalborgDPMWidget(parent_dashboard=dashboard,
                            name='Outlet MFM (0-266 sccm)',
                            nickname='MFM',
                            default_serial_port='COM18',
                            gas_options=('N2','Ar','O2','Air'),
                            gas_numbers=(3,1,4,0))
                            #calibration=((0,200),(0,100)))
    dashboard.add_widget(mfm1,row=4,column=2)

    # Add the DFC MFC
    dfc_1 = AalborgDFCWidget(dashboard,'Chlorine MFC (0-200 sccm)','Cl2 MFC','COM15')
    dashboard.add_widget(dfc_1,row=3,column=2)


    # Start the dashboard
    dashboard.start()

run_main_dashboard()

