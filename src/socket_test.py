from pyopticon.socket_client import PyOpticonSocketClient
import time

# Define some functions to try with exec
def test_fn():
    d = get_dashboard()
    v = d.get_field("UV Light","Actual Status")
    do_threadsafe(lambda: print("Light is "+v+"!!!!!"))

l = lambda: print("Hello :D")

# Initialize the socket client
s = PyOpticonSocketClient(handle_errors='exception')

# Do some field gets, sets, and confirms
print(s.get_field("UV Light","Actual Status"))
print(s.set_field("UV Light","Status Selection","On"))
print(s.do_confirm("UV Light"))

time.sleep(10)

# Do an eval
print(s.do_eval("str(get_dashboard().serial_connected)"))

# So some exec's
print(s.do_exec(test_fn))
print(s.do_exec(l))

# Close the dashboard
s.close()

