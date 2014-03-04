=====================
Registering callbacks
=====================

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

.. note::

   This API is experimental in IPython 2.0, and may be revised in future versions.

.. seealso::

   Module :mod:`IPython.core.hooks`
     The older 'hooks' system allows end users to customise some parts of
     IPython's behaviour.
   
   :doc:`inputtransforms`
     By registering input transformers that don't change code, you can monitor
     what is being executed.
