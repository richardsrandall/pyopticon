import socket
import time
import json
import inspect

class PyOpticonSocketClient:

    def __init__(self,**kwargs):
        socket_number = 12345 if not 'socket_number' in kwargs.keys() else kwargs['socket_number']
        handle_errors = 'none' if not 'handle_errors' in kwargs.keys() else kwargs['handle_errors']
        if handle_errors not in ['none','print','exception']:
            raise Exception("handle_errors must be 'none', 'print', or 'exception'")
        self.socket_obj = socket.socket()
        self.socket_obj.connect(('127.0.0.1',socket_number))
        self.socket_obj.settimeout(5)
        self.handle_errors=handle_errors
        print("Socket opened successfully.")

    def check_errors(self,source,result):
        if result[:5]!="Error":
            return
        if self.handle_errors=='none':
            return
        elif self.handle_errors=='print':
            print("In "+source+", "+result)
        elif self.handle_errors=='exception':
            raise Exception("In "+source+", "+result)

    def query_socket(self,to_send):
        self.socket_obj.send(json.dumps(to_send).encode())
        result =  self.socket_obj.recv(1024).decode()
        self.check_errors(to_send['cmd'],result)
        return result

    def get_field(self,widget_nickname,field_name,printout=True):
        to_send = {'cmd':"Get",'widget_nickname':widget_nickname,'field_name':field_name,'printout':printout}
        result = self.query_socket(to_send)
        return result

    def set_field(self,widget_nickname,field_name,new_value,printout=True):
        to_send = {'cmd':"Set",'widget_nickname': widget_nickname,'field_name':field_name,'new_value':new_value,'printout':printout}
        result = self.query_socket(to_send)
        return result

    def do_confirm(self,widget_nickname,printout=True):
        to_send = {'cmd':"Confirm",'widget_nickname':widget_nickname,'printout':printout}
        result = self.query_socket(to_send)
        return result

    def do_eval(self,expression,printout=True):
        to_send = {'cmd':"Eval",'code':expression,'printout':printout}
        result = self.query_socket(to_send)
        return result

    def do_exec(self,fn,printout=True):
        code =  inspect.getsource(fn)
        to_send = {'cmd':"Exec",'code':code,'printout':printout}
        result = self.query_socket(to_send)
        return result

    def close(self):
        self.socket_obj.send(json.dumps({'cmd':"Close"}).encode())
        self.socket_obj.close()
        print("Socket closed successfully.")

