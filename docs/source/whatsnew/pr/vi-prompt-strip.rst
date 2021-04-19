Automatic Vi prompt stripping
=============================

When pasting code into IPython, it will strip the leading prompt characters if
there are any. For example, you can paste the following code into the console -
it will still work, even though each line is prefixed with prompts (`In`,
`Out`)::

    In [1]: 2 * 2 == 4
    Out[1]: True

    In [2]: print("This still works as pasted")


Previously, this was not the case for the Vi-mode prompts::

    In [1]: [ins] In [13]: 2 * 2 == 4
       ...: Out[13]: True
       ...: 
      File "<ipython-input-1-727bb88eaf33>", line 1
        [ins] In [13]: 2 * 2 == 4
              ^
    SyntaxError: invalid syntax

This is now fixed, and Vi prompt prefixes - ``[ins]`` and ``[nav]`` -  are
skipped just as the normal ``In`` would be.

IPython shell can be started in the Vi mode using ``ipython
--TerminalInteractiveShell.editing_mode=vi``
