Making simple Python wrapper kernels
====================================

.. versionadded:: 3.0

You can now re-use the kernel machinery in IPython to easily make new kernels.
This is useful for languages that have Python bindings, such as `Octave
<http://www.gnu.org/software/octave/>`_ (via
`Oct2Py <http://blink1073.github.io/oct2py/docs/index.html>`_), or languages
where the REPL can be controlled in a tty using `pexpect <http://pexpect.readthedocs.org/en/latest/>`_,
such as bash.

Required steps
--------------

Subclass :class:`IPython.kernel.zmq.kernelbase.KernelBase`, and implement the
following methods and attributes:

.. class:: MyKernel

   .. attribute:: implementation
                  implementation_version
                  language
                  language_version
                  banner
    
     Information for :ref:`msging_kernel_info` replies. 'Implementation' refers
     to the kernel (e.g. IPython), and 'language' refers to the language it
     interprets (e.g. Python). The 'banner' is displayed to the user in console
     UIs before the first prompt. All of these values are strings.

   .. method:: do_execute(code, silent, store_history=True, user_expressions=None, allow_stdin=False)
   
     Execute user code.
     
     :param str code: The code to be executed.
     :param bool silent: Whether to display output.
     :param bool store_history: Whether to record this code in history and
         increase the execution count. If silent is True, this is implicitly
         False.
     :param dict user_expressions: Mapping of names to expressions to evaluate
         after the code has run. You can ignore this if you need to.
     :param bool allow_stdin: Whether the frontend can provide input on request
         (e.g. for Python's :func:`raw_input`).
     
     Your method should return a dict containing the fields described in
     :ref:`execution_results`. To display output, it can send messages
     using :meth:`~IPython.kernel.zmq.kernelbase.KernelBase.send_response`.
     See :doc:`messaging` for details of the different message types.

To launch your kernel::

    from IPython.kernel.zmq.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=MyKernel)

Optional steps
--------------

You can override a number of other methods to improve the functionality of your
kernel. All of these methods should return a dictionary as described in the
relevant section of the :doc:`messaging spec <messaging>`.

.. class:: MyKernel

   .. method:: do_complete(code, cusor_pos)

     Code completion
     
     :param str code: The code already present
     :param int cursor_pos: The position in the code where completion is requested
     
     .. seealso::
     
        :ref:`msging_completion` messages

   .. method:: do_inspect(code, cusor_pos, detail_level=0)

     Object inspection
     
     :param str code: The code
     :param int cursor_pos: The position in the code where inspection is requested
     :param int detail_level: 0 or 1 for more or less detail. In IPython, 1 gets
         the source code.
     
     .. seealso::
     
        :ref:`msging_inspection` messages

   .. method:: do_history(hist_access_type, output, raw, session=None, start=None, stop=None, n=None, pattern=None, unique=False)

     History access

     .. seealso::
     
        :ref:`msging_history` messages

   .. method:: do_shutdown(restart)

     Shutdown the kernel. You only need to handle your own clean up - the kernel
     machinery will take care of cleaning up its own things before stopping.
     
     :param bool restart: Whether the kernel will be started again afterwards
     
     .. seealso::
     
        :ref:`msging_shutdown` messages
