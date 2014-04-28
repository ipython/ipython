* Adds a ``use_cloudpickle`` method to ``DirectView`` objects, which works like
  ``view.use_dill()``, but causes the ``cloudpickle`` module from PiCloud's
  `cloud`__ library to be used rather than dill or the builtin pickle module.

  __ https://pypi.python.org/pypi/cloud
