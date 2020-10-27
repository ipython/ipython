Autosuggestion is a very useful feature available in `fish <https://fishshell.com/>`__, `zsh <https://en.wikipedia.org/wiki/Z_shell>`__, and `prompt-toolkit <https://python-prompt-toolkit.readthedocs.io/en/master/pages/asking_for_input.html#auto-suggestion>`__.

`Ptpython <https://github.com/prompt-toolkit/ptpython#ptpython>`__ allows users to enable this feature in
`ptpython/config.py <https://github.com/prompt-toolkit/ptpython/blob/master/examples/ptpython_config/config.py#L90>`__.

This feature allows users to accept autosuggestions with ctrl e, ctrl f,
or right arrow as described below.

1. Start ipython

.. image:: ../_images/auto_suggest_prompt_no_text.png

2. Run ``print("hello")``

.. image:: ../_images/auto_suggest_print_hello_suggest.png

3. Press p to see the autosuggestion

.. image:: ../_images/auto_suggest_print_hello_suggest.png

4. Press ctrl f, or ctrl e, or right arrow to accept the suggestion

.. image:: ../_images/auto_suggest_print_hello.png

You can also complete word by word:

1. Run ``def say_hello(): print("hello")``

.. image:: ../_images/auto_suggest_second_prompt.png

2. Press d to see the autosuggestion

.. image:: ../_images/audo_suggest_d_phantom.png

3. Press alt f to accept to accept the first word of the suggestion

.. image:: ../_images/auto_suggest_def_phantom.png

Importantly, this feature does not interfere with tab completion:

1. After running ``def say_hello(): print("hello")``, press d

.. image:: ../_images/audo_suggest_d_phantom.png

2. Press Tab to start tab completion

.. image:: ../_images/auto_suggest_d_completions.png

3A. Press Tab again to select the first option

.. image:: ../_images/auto_suggest_def_completions.png

3B. Press alt f to accept to accept the first word of the suggestion

.. image:: ../_images/auto_suggest_def_phantom.png

3C. Press ctrl f or ctrl e to accept the entire suggestion

.. image:: ../_images/auto_suggest_match_parens.png

To install a version of ipython with autosuggestions enabled, run:

``pip install git+https://github.com/mskar/ipython@auto_suggest``

Currently, autosuggestions are only shown in the emacs or vi insert editing modes:

- The ctrl e, ctrl f, and alt f shortcuts work by default in emacs mode.
- To use these shortcuts in vi insert mode, you will have to create `custom keybindings in your config.py <https://github.com/mskar/setup/commit/2892fcee46f9f80ef7788f0749edc99daccc52f4/>`__.

