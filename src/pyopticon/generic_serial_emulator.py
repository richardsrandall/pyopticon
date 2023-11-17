
class GenericSerialEmulator:
    """Serial emulators are designed to 'emulate' a Pyserial Serial object with a wired connection to a certain type of physical device. 
    This lets us test and develop widgets without access to the physical device they represent, e.g. while at home, and then only do a final 
    round of debugging on the computer to which the physical device is attached. It's also useful for demonstrating a dashboard outside of a lab setting.\n
    
    Widgets only call a few of a Serial object's methods (write, reset_input_buffer, readline, readlines, and close). Therefore, it's pretty easy to make an 
    object which is, for a dashboard's purposes, indistinguishable from a Serial object. The idea is that a serial emulator accepts queries and responds to them as if 
    it were an actual machine. For instance, a thermocouple emulator might receive the query 'C\\\\r' asking for the temperature in C, to which it might respond with a 
    hardcoded value of '23\\\\r' as if it were an actual thermocouple adapter. You can make emulators complicated, e.g. tracking when a flow setpoint change is commanded and then 
    returning a flow reading near that setpoint, or very simple, e.g. ignoring any setpoint commands and just returning the same flow reading regardless. Often simple ones suffice.\n
    
    The tutorials and the majumdar_lab_widgets package contain a bit more inspiration for what a serial emulator can look like.
    """

    def write(self, text):
        """Write text to the serial emulator as if it were a Pyserial Serial object. If you want the emulator to ignore all queries and commands, just don't override this method.
        
        :param text: The text to 'write,' usually encoded as ascii bytes.
        :type text: bytes
        """
        return
    
    def reset_input_buffer(self):
        """Reset the serial emulator's input buffer, if it has one, as if it were a Pyserial Serial object"""
        return

    def readlines(self):
        """Read all lines in list form from the serial emulator's input buffer as if it were a Pyserial Serial object, and then clear the buffer. 
        If this method is called but hasn't been overridden in a subclass, something is probably wrong.
        
        :return: A list of all lines (usually text encoded as ascii bytes) currently in the emulator's input buffer.
        :rtype: list
        """
        print("Warning: readlines called on a serial emulator with no readline method implemented.")
        return []

    def readline(self):
        """Read the next line, usually encoded as ascii bytes, from the serial emulator's input buffer as if it were a Pyserial Serial object. Pop that line from the buffer. 
        If this method is called but hasn't been overridden in a subclass, something is probably wrong.
        
        :return: The next line in the serial emulator's input buffer.
        :rtype: bytes
        """
        print("Warning: readline called on a serial emulator with no readline method implemented.")
        return b''
    
    def close(self):
        """Close the serial emulator as if it were a Pyserial Serial object."""
        return