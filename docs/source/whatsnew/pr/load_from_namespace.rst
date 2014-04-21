Adds object inspection to %load magic so that source for objects in user or global namespaces can be loaded. To enable searching the namespace, use the ``-n`` option.

.. sourcecode:: ipython

    In [1]: %load -n my_module.some_function

