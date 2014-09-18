* It's now possible to provide mechanisms to integrate IPython with other event
  loops, in addition to the ones we already support. This lets you run GUI code
  in IPython with an interactive prompt, and to embed the IPython
  kernel in GUI applications. See :doc:`/config/eventloops` for details. As part
  of this, the direct ``enable_*`` and ``disable_*`` functions for various GUIs
  in :mod:`IPython.lib.inputhook` have been deprecated in favour of
  :meth:`~.InputHookManager.enable_gui` and :meth:`~.InputHookManager.disable_gui`.
