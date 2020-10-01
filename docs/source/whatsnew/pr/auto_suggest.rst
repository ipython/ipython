Autosuggestion is a very useful feature available in `fish <https://fishshell.com/>`__, `zsh <https://en.wikipedia.org/wiki/Z_shell>`__, and `prompt-toolkit <https://python-prompt-toolkit.readthedocs.io/en/master/pages/asking_for_input.html#auto-suggestion>`__.

`Ptpython <https://github.com/prompt-toolkit/ptpython#ptpython>`__ allows users to enable this feature in
`ptpython/config.py <https://github.com/prompt-toolkit/ptpython/blob/master/examples/ptpython_config/config.py#L90>`__.

This feature allows users to accept autosuggestions with ctrl e, ctrl f,
or right arrow as described below.

1. Start ipython

|image|

2. Run ``print("hello")``

|image1|

3. Press p to see the autosuggestion

|image2|

4. Press ctrl f, or ctrl e, or right arrow to accept the suggestion

|image3|

You can also complete word by word:

1. Run ``def say_hello(): print("hello")``

|image4|

2. Press d to see the autosuggestion

|image5|

3. Press alt f to accept to accept the first word of the suggestion

|image6|

Importantly, this feature does not interfere with tab completion:

1. After running ``def say_hello(): print("hello")``, press d

|image7|

2. Press Tab to start tab completion

|image8|

3A. Press Tab again to select the first option

|image9|

3B. Press alt f to accept to accept the first word of the suggestion

|image10|

3C. Press ctrl f or ctrl e to accept the entire suggestion

|image11|

To install a version of ipython with autosuggestions enabled, run:

``pip install git+https://github.com/mskar/ipython@auto_suggest``

Currently, autosuggestions are only shown in the emacs or vi insert editing modes:

- The ctrl e, ctrl f, and alt f shortcuts work by default in emacs mode.
- To use these shortcuts in vi insert mode, you will have to create `custom keybindings in your config.py <https://github.com/mskar/setup/commit/2892fcee46f9f80ef7788f0749edc99daccc52f4/>`__.

.. |image| image:: https://user-images.githubusercontent.com/13444106/94700432-76580100-0309-11eb-8798-040d47d1a540.png
.. |image1| image:: https://user-images.githubusercontent.com/13444106/94700528-91c30c00-0309-11eb-920d-4ef8aa79d79a.png
.. |image2| image:: https://user-images.githubusercontent.com/13444106/94700681-bf0fba00-0309-11eb-94bd-bbddf4805da2.png
.. |image3| image:: https://user-images.githubusercontent.com/13444106/94700883-fd0cde00-0309-11eb-9aa8-17270951f021.png
.. |image4| image:: https://user-images.githubusercontent.com/13444106/94704474-f54f3880-030d-11eb-9d73-fa10ced850be.png
.. |image5| image:: https://user-images.githubusercontent.com/13444106/94704519-fe400a00-030d-11eb-8b73-3c35ffaf1a9d.png
.. |image6| image:: https://user-images.githubusercontent.com/13444106/94704602-14e66100-030e-11eb-90fc-d930463f52de.png
.. |image7| image:: https://user-images.githubusercontent.com/13444106/94704519-fe400a00-030d-11eb-8b73-3c35ffaf1a9d.png
.. |image8| image:: https://user-images.githubusercontent.com/13444106/94704969-80303300-030e-11eb-8379-6bff94582849.png
.. |image9| image:: https://user-images.githubusercontent.com/13444106/94705023-90481280-030e-11eb-9cf7-76170d1004b9.png
.. |image10| image:: https://user-images.githubusercontent.com/13444106/94704602-14e66100-030e-11eb-90fc-d930463f52de.png
.. |image11| image:: https://user-images.githubusercontent.com/13444106/94705115-ab1a8700-030e-11eb-9dee-da98fccca0a6.png
