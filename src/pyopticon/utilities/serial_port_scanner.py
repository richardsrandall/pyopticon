import serial
import time
import serial.tools.list_ports

def scan_serial_ports():
    """ Enter an infinite loop in which anytime a serial port appears or disappears, its name is printed to the console. 
    This is useful for figuring out which physical devices are represented by which serial ports. 
    This function should be invoked from some kind of Python shell like IDLE so you can see its printed outputs. 
    """

    print("Running serial port scanning tool.")
    print("If you plug or unplug a serial device, this script will print which serial port it was.\n")

    old_port_names = set()
    while True:
        time.sleep(1)
        ports = serial.tools.list_ports.comports()
        new_port_names = set(port.name for port in ports)
        ports_added = [x for x in new_port_names if x not in old_port_names]
        ports_removed = [x for x in old_port_names if x not in new_port_names]
        newline_flag = False
        old_port_names = new_port_names
        if len(ports_added)>0:
            ports_added_str = ', '.join(sorted(list(ports_added)))
            print("COM Ports Added: "+ports_added_str)
            newline_flag = True
        if len(ports_removed)>0:
            ports_removed_str = ', '.join(sorted(list(ports_removed)))
            print("COM Ports Removed: "+ports_removed_str)
            newline_flag = True
        if newline_flag:
            print("")

