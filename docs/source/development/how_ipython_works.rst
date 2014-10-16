How IPython Works
=================

Terminal IPython
----------------

When you type ``ipython``, you get the original IPython interface, running in
the terminal. It does something like this::

    while True:
        code = input(">>> ")
        exec(code)

Of course, it's much more complicated, because it has to deal with multi-line
code, tab completion using :mod:`readline`, magic commands, and so on. But the
model is like that: prompt the user for some code, and when they've entered it,
exec it in the same process.

The IPython Kernel
------------------

All the other interfaces—the Notebook, the Qt console, ``ipython console`` in
the terminal, and third party interfaces—use the IPython Kernel. This is a
separate process which is responsible for running user code, and things like
computing possible completions. Frontends communicate with it using JSON
messages sent over ZeroMQ sockets; the protocol they use is described in
:doc:`messaging`.

The core execution machinery for the kernel is shared with terminal IPython:

.. image:: figs/ipy_kernel_and_terminal.png

A kernel process can be connected to more than one frontend simultaneously. In
this case, the different frontends will have access to the same variables.

.. TODO: Diagram illustrating this?

This design was intended to allow easy development of different frontends based
on the same kernel, but it also made it possible to support new languages in the
same frontends, by developing kernels in those languages, and we are refining
IPython to make that more practical.

Today, there are two ways to develop a kernel for another language. Wrapper
kernels reuse the communications machinery from IPython, and implement only the
core execution part. Native kernels implement execution and communications in
the target language:

.. image:: figs/other_kernels.png

.. seealso::

   :doc:`kernels`
   
   :doc:`wrapperkernels`


