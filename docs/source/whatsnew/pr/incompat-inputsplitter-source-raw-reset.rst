* :class:`IPython.core.inputsplitter.IPythonInputSplitter` no longer has a method
  ``source_raw_reset()``, but gains :meth:`~IPython.core.inputsplitter.IPythonInputSplitter.raw_reset`
  instead. Use of ``source_raw_reset`` can be replaced with::
  
      raw = isp.source_raw
      transformed = isp.source_reset()
