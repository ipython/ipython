:orphan:

Writing code for Python 2 and 3
===============================

.. module:: IPython.utils.py3compat
   :synopsis: Python 2 & 3 compatibility helpers


IPython 6 requires Python 3, so our compatibility module
``IPython.utils.py3compat`` is deprecated. In most cases, we recommend you use
the `six module <https://pythonhosted.org/six/>`__ to support compatible code.
This is widely used by other projects, so it is familiar to many developers and
thoroughly battle-tested.

Our ``py3compat`` module provided some more specific unicode conversions than
those offered by ``six``. If you want to use these, copy them into your own code
from IPython 5.x. Do not rely on importing them from IPython, as the module may
be removed in the future.

.. seealso::

   `Porting Python 2 code to Python 3 <https://docs.python.org/3/howto/pyporting.html>`_
     Official information in the Python docs.

   `Python-Modernize <http://python-modernize.readthedocs.io/en/latest/>`_
     A tool which helps make code compatible with Python 3.

   `Python-Future <http://python-future.org/>`_
     Another compatibility tool, which focuses on writing code for Python 3 and
     making it work on Python 2.
