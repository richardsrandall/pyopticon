import socket
import time
import json
import inspect

class PyOpticonSocketClient:
    """Class representing a client-side socket connection to a PyOpticon dashboard. Can be used to send various commands and 
    queries to the dashboard from a separate Python script.
    
    :param socket_number: The port on which to open the socket connection. Defaults to 12345.
    :type socket_number: int, optional
    :param handle_errors: How to handle errors reported by the dashboard when attempting to execute a socket command. 'none' does nothing, 'print' prints a warning to console but continues executing, 'exception' raises an exception. Defaults to 'none'.
    :type handle_errors: str, optional
    """

    def __init__(self,**kwargs):
        """Constructor for a socket client object."""
        socket_number = 12345 if not 'socket_number' in kwargs.keys() else kwargs['socket_number']
        handle_errors = 'none' if not 'handle_errors' in kwargs.keys() else kwargs['handle_errors']
        if handle_errors not in ['none','print','exception']:
            raise Exception("handle_errors must be 'none', 'print', or 'exception'")
        self.socket_obj = socket.socket()
        self.socket_obj.connect(('127.0.0.1',socket_number))
        self.socket_obj.settimeout(5)
        self.handle_errors=handle_errors
        print("Socket opened successfully.")

    def _check_errors(self,source,result):
        """Checks a string returned by the dashboard for whether it's an error message (beginning with 'Error: ') and, if so, processes it.
        
        :param source: The command, e.g. 'get', that the dashboard was trying to execute.
        :type source: str
        :param result: The string that the dashboard sent through the socket as its reply, which may or may not be an error message.
        :type result: str
        """
        if result[:5]!="Error":
            return
        if self.handle_errors=='none':
            return
        elif self.handle_errors=='print':
            print("In "+source+", "+result)
        elif self.handle_errors=='exception':
            raise Exception("In "+source+", "+result)

    def _query_socket(self,to_send):
        """Converts a dict to a JSON string and sends it through the socket.
        
        :param to_send: The dict to send to the dashboard.
        :type to_send: dict"""
        self.socket_obj.send(json.dumps(to_send).encode())
        result =  self.socket_obj.recv(1024).decode()
        self._check_errors(to_send['cmd'],result)
        return result

    def get_field(self,widget_nickname,field_name,printout=True):
        """Gets the current value of a field from the dashboard via the socket.
        
        :param widget_nickname: The nickname of the widget to query
        :type widget_nickname: str
        :param field_name: The field to query
        :type field_name: str
        :param printout: Whether the dashboard should print to its own console a record that the socket command was received. Defaults to True.
        :type printout: bool, optional
        :return: The current value of the specified field.
        :rtype: str"""
        to_send = {'cmd':"Get",'widget_nickname':widget_nickname,'field_name':field_name,'printout':printout}
        result = self._query_socket(to_send)
        return result

    def set_field(self,widget_nickname,field_name,new_value,printout=True):
        """Sets the value of a field to a specified value via the socket.
        
        :param widget_nickname: The nickname of the widget whose field to set
        :type widget_nickname: str
        :param field_name: The field to set
        :type field_name: str
        :type new_value: The value to which to set the field
        :type new_value: str
        :param printout: Whether the dashboard should print to its own console a record that the socket command was received. Defaults to True.
        :type printout: bool, optional
        """
        to_send = {'cmd':"Set",'widget_nickname': widget_nickname,'field_name':field_name,'new_value':new_value,'printout':printout}
        result = self._query_socket(to_send)
        return result

    def do_confirm(self,widget_nickname,printout=True):
        """Executes a widget's 'confirm' method via the socket.
        
        :param widget_nickname: The nickname of the widget to confirm
        :type widget_nickname: str
        :param printout: Whether the dashboard should print to its own console a record that the socket command was received. Defaults to True.
        :type printout: bool, optional
        """
        to_send = {'cmd':"Confirm",'widget_nickname':widget_nickname,'printout':printout}
        result = self._query_socket(to_send)
        return result

    def do_eval(self,expression,printout=True):
        """Tells the dashboard to evaluate an expression and return the result. Eval is run in a namespace containing the methods 
        get_dashboard(), which returns a dashboard object, and do_threadsafe(f), which executes a function f in the main GUI thread.
        
        :param expression: The expression to evaluate
        :type widget_nickname: str
        :param printout: Whether the dashboard should print to its own console a record that the socket command was received. Defaults to True.
        :type printout: bool, optional
        """
        to_send = {'cmd':"Eval",'code':expression,'printout':printout}
        result = self._query_socket(to_send)
        return result

    def do_exec(self,fn,printout=True):
        """Tells the dashboard to execute a given function. Exec is run in a namespace containing the methods 
        get_dashboard(), which returns a dashboard object, and do_threadsafe(f), which executes a function f in the main GUI thread. 
        
        The code to execute should be supplied as a function. The object uses the 'inspect' module to get the function's source as a 
        string and pass it through the socket. This lets you benefit from normal syntax highlighting in writing your function, 
        rather than having to define it as a string with a bunch of escaped newline and tab characters in it. Due to the 
        'inspect' module's limitations, the function must be defined separately and then passed to do_exec, rather than being 
        defined inline with the do_exec call using a lambda function. E.g., s.do_exec(lambda: print("Hi")) is invalid. See the tutorial.

        :param expression: The code to run
        :type widget_nickname: function or str
        :param printout: Whether the dashboard should print to its own console a record that the socket command was received. Defaults to True.
        :type printout: bool, optional
        """
        code =  inspect.getsource(fn)
        to_send = {'cmd':"Exec",'code':code,'printout':printout}
        result = self._query_socket(to_send)
        return result

    def close(self):
        """Send a message via the socket telling the Dashboard to close the socket on its end. Close the socket connection on the client end."""
        self.socket_obj.send(json.dumps({'cmd':"Close"}).encode())
        self.socket_obj.close()
        print("Socket closed successfully.")

