Gallery
========================

A pre-alpha prototype PyOpticon dashboard in operation in the Majumdar Lab at Stanford, 
with its desktop icon visible and with both data logging and an automation script active:

.. image:: img/rv1.png
    :alt: A screenshot of a PyOpticon dashboard in operation

A demo automation script, which normally would live in its own .py file, that flickers a UV light on and off a few times:

.. code-block:: python

    # Start the script
    schedule_function(lambda: print("Here we go!"))
    schedule_delay('0:01:00')
    # Switch the UV light on and off a few times
    schedule_function(lambda: print("Beginning light flickering"))
    for i in range(5):
        schedule_action('UV Light','Light Status Selection','On')
        schedule_delay('0:00:05')
        schedule_action('UV Light','Light Status Selection','Off')
        schedule_delay('0:00:05')
    # Confirm that the script finished successfully
    schedule_function(lambda: print("All done!"))