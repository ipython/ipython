=======================
Built-in magic commands
=======================

.. note::

    To Jupyter users: Magics are specific to and provided by the IPython kernel.
    Whether Magics are available on a kernel is a decision that is made by
    the kernel developer on a per-kernel basis. To work properly, Magics must
    use a syntax element which is not valid in the underlying language. For
    example, the IPython kernel uses the `%` syntax element for Magics as `%`
    is not a valid unary operator in Python. However, `%` might have meaning in
    other languages.

Here is the help auto-generated from the docstrings of all the available Magics
functions that IPython ships with. 

You can create and register your own Magics with IPython. You can find many user
defined Magics on `PyPI <https://pypi.org>`_. Feel free to publish your own and
use the ``Framework :: IPython`` trove classifier. 


.. include:: magics-generated.txt
