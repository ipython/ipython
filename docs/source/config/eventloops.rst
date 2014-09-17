================================
Integrating with GUI event loops
================================

When the user types ``%gui qt``, IPython integrates itself with the Qt event
loop, so you can use both a GUI and an interactive prompt together. IPython
supports a number of common GUI toolkits, but from IPython 3.0, it is possible
to integrate other event loops without modifying IPython itself.

Terminal IPython handles event loops very differently from the IPython kernel,
so different steps are needed to integrate with each.

Event loops in the terminal
---------------------------

In the terminal, IPython uses a blocking Python function to wait for user input.
However, the Python C API provides a hook, :c:func:`PyOS_InputHook`, which is
called frequently while waiting for input. This can be set to a function which
briefly runs the event loop and then returns.

IPython provides Python level wrappers for setting and resetting this hook. To
use them, subclass :class:`IPython.lib.inputhook.InputHookBase`, and define
an ``enable(app=None)`` method, which initialises the event loop and calls
``self.manager.set_inputhook(f)`` with a function which will briefly run the
event loop before exiting. Decorate the class with a call to
:func:`IPython.lib.inputhook.register`::

    from IPython.lib.inputhook import register, InputHookBase

    @register('clutter')
    class ClutterInputHook(InputHookBase):
        def enable(self, app=None):
            self.manager.set_inputhook(inputhook_clutter)

You can also optionally define a ``disable()`` method, taking no arguments, if
there are extra steps needed to clean up. IPython will take care of resetting
the hook, whether or not you provide a disable method.

The simplest way to define the hook function is just to run one iteration of the
event loop, or to run until no events are pending. Most event loops provide some
mechanism to do one of these things. However, the GUI may lag slightly,
because the hook is only called every 0.1 seconds. Alternatively, the hook can
keep running the event loop until there is input ready on stdin. IPython
provides a function to facilitate this:

.. currentmodule:: IPython.lib.inputhook

.. function:: stdin_ready()

   Returns True if there is something ready to read on stdin.
   
   If this is the case, the hook function should return immediately.
   
   This is implemented for Windows and POSIX systems - on other platforms, it
   always returns True, so that the hook always gives Python a chance to check
   for input.


Event loops in the kernel
-------------------------

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
