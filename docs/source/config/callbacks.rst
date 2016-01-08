.. _events:
.. _callbacks:

==============
IPython Events
==============

Extension code can register callbacks functions which will be called on specific
events within the IPython code. You can see the current list of available
callbacks, and the parameters that will be passed with each, in the callback
prototype functions defined in :mod:`IPython.core.callbacks`.

To register callbacks, use :meth:`IPython.core.events.EventManager.register`.
For example::

    class VarWatcher(object):
        def __init__(self, ip):
            self.shell = ip
            self.last_x = None
        
        def pre_execute(self):
            self.last_x = self.shell.user_ns.get('x', None)
        
        def post_execute(self):
            if self.shell.user_ns.get('x', None) != self.last_x:
                print("x changed!")

    def load_ipython_extension(ip):
        vw = VarWatcher(ip)
        ip.events.register('pre_execute', vw.pre_execute)
        ip.events.register('post_execute', vw.post_execute)


Events
======

These are the events IPython will emit. Callbacks will be passed no arguments, unless otherwise specified.

shell_initialized
-----------------

.. code-block:: python

    def shell_initialized(ipython):
        ...

This event is triggered only once, at the end of setting up IPython.
Extensions registered to load by default as part of configuration can use this to execute code to finalize setup.
Callbacks will be passed the InteractiveShell instance.

pre_run_cell
------------

``pre_run_cell`` fires prior to interactive execution (e.g. a cell in a notebook).
It can be used to note the state prior to execution, and keep track of changes.

pre_execute
-----------

``pre_execute`` is like ``pre_run_cell``, but is triggered prior to *any* execution.
Sometimes code can be executed by libraries, etc. which
skipping the history/display mechanisms, in which cases ``pre_run_cell`` will not fire.

post_run_cell
-------------

``post_run_cell`` runs after interactive execution (e.g. a cell in a notebook).
It can be used to cleanup or notify or perform operations on any side effects produced during execution.
For instance, the inline matplotlib backend uses this event to display any figures created but not explicitly displayed during the course of the cell.


post_execute
------------

The same as ``pre_execute``, ``post_execute`` is like ``post_run_cell``,
but fires for *all* executions, not just interactive ones.


.. seealso::

   Module :mod:`IPython.core.hooks`
     The older 'hooks' system allows end users to customise some parts of
     IPython's behaviour.
   
   :doc:`inputtransforms`
     By registering input transformers that don't change code, you can monitor
     what is being executed.
