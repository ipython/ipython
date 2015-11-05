How IPython works
=================

Terminal IPython
----------------

When you type ``ipython``, you get the original IPython interface, running in
the terminal. It does something like this::

    while True:
        code = input(">>> ")
        exec(code)

Of course, it's much more complex, because it has to deal with multi-line
code, tab completion using :mod:`readline`, magic commands, and so on. But the
model is like that: prompt the user for some code, and when they've entered it,
exec it in the same process. This model is often called a REPL, or
Read-Eval-Print-Loop.

The IPython Kernel
------------------

All the other interfaces—the Notebook, the Qt console, ``ipython console`` in
the terminal, and third party interfaces—use the IPython Kernel. This is a
separate process which is responsible for running user code, and things like
computing possible completions. Frontends communicate with it using JSON
messages sent over `ZeroMQ <http://zeromq.org/>`_ sockets; the protocol they use is described in
:ref:`jupyterclient:messaging`.

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

Wrapper kernels are easier to write quickly for languages that have good Python
wrappers, like `octave_kernel <https://pypi.python.org/pypi/octave_kernel>`_, or
languages where it's impractical to implement the communications machinery, like
`bash_kernel <https://pypi.python.org/pypi/bash_kernel>`_. Native kernels are
likely to be better maintained by the community using them, like
`IJulia <https://github.com/JuliaLang/IJulia.jl>`_ or `IHaskell <https://github.com/gibiansky/IHaskell>`_.

.. seealso::

   :ref:`jupyterclient:kernels`
   
   :doc:`wrapperkernels`

