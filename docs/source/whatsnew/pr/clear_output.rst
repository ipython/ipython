clear_output changes
--------------------

* There is no longer a 500ms delay when calling ``clear_output``.
* The ability to clear stderr and stdout individually was removed.
* A new wait flag that prevents ``clear_output`` from being executed until new 
  output is available.  This eliminates animation flickering by allowing the 
  user to double buffer the output.
* The output div height is remembered when the ``wait=True`` flag is used.
