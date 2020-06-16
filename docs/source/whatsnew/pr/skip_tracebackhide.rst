The default tracebackmode will now skip frames that are marked with
``__tracebackhide__ = True`` and show how many traceback frames have been
skipped. This can be toggled by using :magic:`xmode` with the ``--show`` or
``--hide`` attribute. It will have no effect on non verbose traceback modes. 

The ipython debugger also now understand ``__tracebackhide__`` as well and will
skip hidden frames when displaying. Movement up and down the stack will skip the
hidden frames and will show how many frames were hidden. Internal IPython frames
are also now hidden by default. The behavior can be changed with the
``skip_hidden`` command and accepts "yes", "no", "true" and "false" case
insensitive parameters.
