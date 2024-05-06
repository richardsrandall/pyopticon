from tkinter import *
import serial.tools.list_ports
import platform
import traceback
import socket
import json
import select

# Socket widget
class SocketWidget:
    
    """ This widget manages socket connections from external Python programs. It displays how many sockets are connected and has a few other useful functions.

    :param parent: The dashboard to which this widget will be added.
    :type parent: pyopticon.dashboard.PyOpticonDashboard
    :param port_numbers: A list of int ports on which to open socket server threads.
    :type port_numbers: list
    """

    def __init__(self, parent_dashboard, port_numbers):
        """The constructor for the SocketWidget"""
        
        # Parent is the labGUI object, root is the tkinter root object
        # Set polling interval
        self.parent = parent_dashboard
        self.root = parent_dashboard.get_tkinter_object()
        self.main_color = '#FF7F7F'
        self.port_numbers = port_numbers
        # Widget for all serial connections
        self.frame = Frame(self.root,highlightbackground=self.main_color, highlightcolor=self.main_color, highlightthickness=5)
        self.status_text = StringVar()
        self.sockets_connected = 0
        self.status_text.set("Sockets connected: 0")
        self.status_label = Label(self.frame,textvariable=self.status_text)
        self.status_label.grid(row=1,column=1,sticky='nesw')
        self.disconnect_button = Button(self.frame,text="Force Disconnect",command = self._force_disconnect)
        self.disconnect_button.grid(row=2,column=1,sticky='nesw')
        self.disconnect_button["state"]="disabled"
        self._force_disconnect=False
        print_ports = lambda: print("Available ports for sockets: "+str(self.port_numbers))
        self.help_button = Button(self.frame, text="Print Available Ports to Console", command = print_ports)
        self.help_button.grid(row=3,column=1,sticky='nesw')
        self.time_to_end_thread = False

    # Couple of methods to make the socket counter threadsafe
    def _change_socket_counter(self,change):
        """ Changes the socket counter displayed on the screen and updates the display and frame color accordingly.
        
        :param change: Value to add to the socket counter (+1 or -1)
        :type change: int
        """
        self.sockets_connected+=change
        new_val = "Sockets connected: "+str(self.sockets_connected)
        self.status_text.set(new_val)
        if self.sockets_connected==0:
            self._force_disconnect = False
            self.frame.configure(highlightbackground=self.main_color, highlightcolor=self.main_color)
            self.disconnect_button["state"]="disabled"
        else:
            self.frame.configure(highlightbackground='green', highlightcolor='green')
            self.disconnect_button["state"]="normal"

    def _increment_socket_counter(self):
        """Increments the socket connection counter in a thread-safe way."""
        self.parent.root.after(0,lambda: self._change_socket_counter(1))

    def _decrement_socket_counter(self):
        """Decrements the socket connection counter in a thread-safe way."""
        self.parent.root.after(0,lambda: self._change_socket_counter(-1))

    def get_frame(self):
        """Get the tkinter frame on which this object is drawn.
        
        :return: The widget's tkinter frame
        :rtype: tkinter.Frame
        """
        return self.frame

    def _shutdown_threads(self):
        """Sets a flag that tells the socket processing threads to close themselves at program shutdown."""
        self.time_to_end_thread = True
    
    def _run_one_thread(self,which_port):
        """ Launch a thread that listens on a port for socket connections, handles the various types of commands that 
        may be received on that socket, and shuts down the socket and thread on program close. Also handles ports that are 
        'left hanging' when a client crashes or disconnects without sending a 'Close' method.
        
        :param which_port: The port on which this thread will listen.
        :type which_port: int"""
        # Run the thread that manages the socket connection
        while not self.time_to_end_thread:
            s = socket.socket() #Set up a socket and start listening on it
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.settimeout(1)
            try:
                s.bind(('', which_port))
            except Exception as e: # Bail and end the thread if the socket is taken or otherwise invalid
                print("Socket "+str(which_port)+" could not be opened.")
                return
            s.listen(5)
            try:
                c, addr = s.accept() # Listen for a little while; if no command, return to start of the while loop. Ensures the thread ends promptly when the program shuts down.
            except TimeoutError:
                continue
            print("Connection to socket "+str(which_port)+" from: "+str(addr)) # Got a connection!
            self._increment_socket_counter()
            try:
                while not self.time_to_end_thread and not self._force_disconnect: # Stay in this loop so long as the socket is connected
                    try:
                        c.settimeout(1)#Guarantees the dashboard will close even if a connection is left hanging.
                        rcvdData = c.recv(1024).decode()
                    except TimeoutError:
                        if self.time_to_end_thread:
                            print("Socket "+str(which_port)+" was left hanging on dashboard close; closing it automatically.")
                        continue
                    rcvdDict = json.loads(rcvdData) # Commands are sent in the form of dict's
                    cmd = rcvdDict['cmd']
                    if cmd=="Close":
                        break #Close the socket and wait for a reconnection on the same port
                    try:
                        if cmd=="Get": #Any exceptions raised are dealt with outside the if statement, so this if statement's entries just process commands and do printouts
                            if rcvdDict['printout']:
                                print("Received command on socket "+str(which_port)+": Get "+rcvdDict['field_name']+' in '+rcvdDict['widget_nickname'])
                            sendData=self.parent.get_field(rcvdDict['widget_nickname'],rcvdDict['field_name'])

                        elif cmd=="Set":
                            if rcvdDict['printout']:
                                print("Received command on socket "+str(which_port)+": Set "+rcvdDict['field_name']+' in '+rcvdDict['widget_nickname']+" to "+rcvdDict['new_value'])
                            self.parent.set_field(rcvdDict['widget_nickname'],rcvdDict['field_name'],rcvdDict['new_value'],False)
                            sendData="Success"

                        elif cmd=="Confirm":
                            if rcvdDict['printout']:
                                print("Received command on socket "+str(which_port)+": Confirm in "+rcvdDict['widget_nickname'])
                            self.parent.get_widget_by_nickname(rcvdDict['widget_nickname']).confirm()
                            sendData="Success"

                        elif cmd=="Eval":
                            if rcvdDict['printout']:
                                print("Received command on socket "+str(which_port)+": eval")
                            # Execute the eval in a namespace with a method giving access to the dashboard object
                            sendData=eval(rcvdDict['code'],{'get_dashboard': lambda: self.parent, 'do_threadsafe': (lambda l: self.parent.root.after(0,l))})

                        elif cmd=="Exec": # This is the jankiest and least-recommended socket command, but we include it just in case
                            if rcvdDict['printout']:
                                print("Received command on socket "+str(which_port)+": exec")
                            # Execute the exec in a namespace with a method giving access to the dashboard object
                            code = rcvdDict['code']
                            if 'do_exec' in code:
                                raise Exception("Ignoring do_exec() call: Not allowed to define exec functions inline (e.g. do_exec(lambda x: ...)); please define the function elsewhere (l = lambda x: ..., or def l():...), then do_exec(l).")
                            elif code[:3]=='def':
                                #Replace the first line with a standard name, append line that executes it
                                code = code[code.index('\n')+1:]
                                code = "def to_exec():\n"+code+"\nto_exec()"
                            elif 'lambda' in code:
                                #Replace the first line with a standard name, append line that executes it
                                code = code[code.index('lambda'):]
                                code = "to_exec = "+code+"\nto_exec()"
                            exec(code,{'get_dashboard': lambda: self.parent,'do_threadsafe': (lambda l: self.parent.root.after(0,l)) })
                            sendData="Success"

                    except Exception as e: #All exceptions send 'Error' and the exception name thru the socket and also log the exception as per the dashboard configuration
                        sendData = "Error: "+str(e)
                        if rcvdData!="":
                            self.parent.exc_handler(e,"socket")
                    c.send(sendData.encode())
                print("Socket "+str(which_port)+" closed normally.") #If we reach this part of the loop, if means the socket ended with a 'close' command
                self._decrement_socket_counter()
                c.close()
            except Exception as e: #A socket that's 'left hanging' and then attempts to reconnect triggers a broken pipe exception or similar; we just note it and return to loop start and the connection proceeds as normal
                print("Old socket "+str(which_port)+" appears to have been left hanging; resetting.")
                self._decrement_socket_counter()
                c.close()
    
    def _force_disconnect(self):
        """Force any connected sockets to disconnect, resulting in broken pipe exceptions on the client side."""
        print("Manually disconnecting any connected sockets. Clients will report broken pipes.")
        self._force_disconnect = True