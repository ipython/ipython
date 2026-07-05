================================
Integrating with GUI event loops
================================

When the user types ``%gui qt``, IPython integrates itself with the Qt event
loop, so you can use both a GUI and an interactive prompt together. IPython
supports a number of common GUI toolkits, and it is possible to integrate
other event loops without modifying IPython itself.

Supported event loops include ``qt5``, ``qt6``, ``gtk2``, ``gtk3``, ``gtk4``,
``wx``, ``osx`` and ``tk``. Make sure the event loop you specify matches the
GUI toolkit used by your own code.

.. note::

   ``gtk2`` is deprecated and GTK3 or GTK4 should be used instead for new projects.

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

The kernel runs its own event loop, so event loop integration is handled by
`ipykernel <https://ipykernel.readthedocs.io/>`__ rather than by IPython
itself.

To integrate a new toolkit, write a function that takes a single argument,
the IPython kernel instance, and starts the GUI event loop. The function is
responsible for arranging to give control back to the kernel when there is
work for it to do — for example by watching the file descriptor of the
kernel's shell socket from the GUI event loop, or by yielding back to the
kernel at least every ``kernel._poll_interval`` seconds.

Decorate this function with :func:`ipykernel.eventloops.register_integration`,
passing in the names you wish to register it for; if you register it as
``'foo'``, users can enable the integration by running ``%gui foo``. A
matching exit function, which stops the GUI event loop so that the kernel can
switch to another one, can be registered with the ``@loop_foo.exit``
decorator.

Writing such an integration robustly is beyond the scope of this document;
the existing integrations in :mod:`ipykernel.eventloops` (Qt, Tk, GTK, wx,
Cocoa, asyncio) are the best reference.
