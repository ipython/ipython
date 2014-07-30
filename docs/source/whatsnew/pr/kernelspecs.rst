Using different kernels
=======================

.. image:: ../_images/kernel_selector_screenshot.png
   :alt: Screenshot of notebook kernel selection dropdown menu
   :align: center

You can now choose a kernel for a notebook within the user interface, rather
than starting up a separate notebook server for each kernel you want to use. The
syntax highlighting adapts to match the language you're working in.

Information about the kernel is stored in the notebook file, so when you open a
notebook, it will automatically start the correct kernel.

It is also easier to use the Qt console and the terminal console with other
kernels, using the --kernel flag::

    ipython qtconsole --kernel bash
    ipython console --kernel bash
    
    # To list available kernels
    ipython kernelspec list

Kernel authors should see :ref:`kernelspecs` for how to register their kernels
with IPython so that these mechanisms work.
