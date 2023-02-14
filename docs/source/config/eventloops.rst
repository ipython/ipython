================================
Integrating with GUI event loops
================================

When the user types ``%gui qt``, IPython integrates itself with the Qt event
loop, so you can use both a GUI and an interactive prompt together. IPython
supports a number of common GUI toolkits, but from IPython 3.0, it is possible
to integrate other event loops without modifying IPython itself.

Supported event loops include ``qt5``, ``qt6``, ``gtk2``, ``gtk3``, ``gtk4``,
``wx``, ``osx`` and ``tk``. Make sure the event loop you specify matches the
GUI toolkit used by your own code.

To make IPython GUI event loop integration occur automatically at every
startup, set the ``c.InteractiveShellApp.gui`` configuration key in your
IPython profile (see :ref:`setting_config`).

If the event loop you use is supported by IPython, turning on event loop
integration follows the steps just described whether you use Terminal IPython
or an IPython kernel.

However, the way Terminal IPython handles event loops is very different from
the way IPython kernel does, so if you need to integrate with a new kind of
event loop, different steps are needed to integrate with each.

Integrating with a new event loop in the terminal
-------------------------------------------------

.. versionchanged:: 5.0

   There is a new API for event loop integration using prompt_toolkit.

In the terminal, IPython uses prompt_toolkit to prompt the user for input.
prompt_toolkit provides hooks to integrate with an external event loop.

To integrate an event loop, define a function which runs the GUI event loop
until there is input waiting for prompt_toolkit to process. There are two ways
to detect this condition::

    # Polling for input.
    def inputhook(context):
        while not context.input_is_ready():
            # Replace this with the appropriate call for the event loop:
            iterate_loop_once()

    # Using a file descriptor to notify the event loop to stop.
    def inputhook2(context):
        fd = context.fileno()
        # Replace the functions below with those for the event loop.
        add_file_reader(fd, callback=stop_the_loop)
        run_the_loop()

Once you have defined this function, register it with IPython:

.. currentmodule:: IPython.terminal.pt_inputhooks

.. function:: register(name, inputhook)

   Register the function *inputhook* as the event loop integration for the
   GUI *name*. If ``name='foo'``, then the user can enable this integration
   by running ``%gui foo``.


Integrating with a new event loop in the kernel
-----------------------------------------------

The kernel runs its own event loop, so it's simpler to integrate with others.
IPython allows the other event loop to take control, but it must call
:meth:`IPython.kernel.zmq.kernelbase.Kernel.do_one_iteration` periodically.

To integrate with this, write a function that takes a single argument,
the IPython kernel instance, arranges for your event loop to call
``kernel.do_one_iteration()`` at least every ``kernel._poll_interval`` seconds,
and starts the event loop.

Decorate this function with :func:`IPython.kernel.zmq.eventloops.register_integration`,
passing in the names you wish to register it for. Here is a slightly simplified
version of the Tkinter integration already included in IPython::

    @register_integration('tk')
    def loop_tk(kernel):
        """Start a kernel with the Tk event loop."""
        from tkinter import Tk

        # Tk uses milliseconds
        poll_interval = int(1000*kernel._poll_interval)
        # For Tkinter, we create a Tk object and call its withdraw method.
        class Timer(object):
            def __init__(self, func):
                self.app = Tk()
                self.app.withdraw()
                self.func = func

            def on_timer(self):
                self.func()
                self.app.after(poll_interval, self.on_timer)

            def start(self):
                self.on_timer()  # Call it once to get things going.
                self.app.mainloop()

        kernel.timer = Timer(kernel.do_one_iteration)
        kernel.timer.start()

Some event loops can go one better, and integrate checking for messages on the
kernel's ZMQ sockets, making the kernel more responsive than plain polling. How
to do this is outside the scope of this document; if you are interested, look at
the integration with Qt in :mod:`IPython.kernel.zmq.eventloops`.
