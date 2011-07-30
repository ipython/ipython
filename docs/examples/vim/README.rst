###########
vim-ipython
###########

A two-way integration between Vim and IPython 0.11+

author: Paul Ivanov (http://pirsquared.org)

github: http://github.com/ivanov/vim-ipython

demo: http://pirsquared.org/vim-ipython/

Using this plugin, you can send lines or whole files for IPython to
execute, and also get back object introspection and word completions in
Vim, like what you get with: ``object?<enter>`` and ``object.<tab>`` in
IPython.

The big change from previous versions of ``ipy.vim`` is that it no longer
requires the brittle ipy_vimserver.py instantiation, and since it uses
just vim and python, it is platform independent (i.e. should work even
on windows, unlike the previous \*nix only solution)


-----------------
Quickstart Guide:
-----------------
Start ``ipython qtconsole`` and copy the connection string.
Source ``ipy.vim`` file, which provides new IPython command::

  :source ipy.vim  
  (or copy it to ~/.vim/ftplugin/python to load automatically)

  :IPythonClipboard   
  (or :IPythonXSelection if you're using X11 without having to copy)

The :IPython command allows you to put the full string, e.g.::

  :IPython --existing --shell=41882 --iopub=43286 --stdin=34987 --hb=36697

The ``:IPythonClipboard`` command just uses the ``+`` register to get the
connection string, whereas ``:IPythonXSelection`` uses the ``*`` register

------------------------
Sending lines to IPython
------------------------
Now type out a line and send it to IPython using ``<Ctrl-S>`` from Command mode::

  import os

You should see a notification message confirming the line was sent, along
with the input number for the line, like so ``In[1]: import os``.

``<Ctrl-S>`` also works from insert mode, but doesn't show notification

It also works blockwise in Visual Mode. Strip the leading double quotes and
send these lines using ``<Ctrl-S>``::

  import this,math # secret decoder ring
  a,b,c,d,e,f,g,h,i = range(1,10)
  code =(c,a,d,a,e,i,)
  msg = '...jrer nyy frag sebz Ivz.\nIvz+VClguba=%fyl '+this.s.split()[g]
  decode=lambda x:"\n"+"".join([this.d.get(c,c) for c in x])+"!"
  format=lambda x:'These lines:\n  '+'\n  '.join([l for l in x.splitlines()])
  secret_decoder = lambda a,b: format(a)+decode(msg)%str(b)[:-1]
  '%d'*len(code)%code == str(int(math.pi*1e5))

Then, go to the qtconsole and run this line::
  
  print secret_decoder(_i,_)

You can also send whole files to IPython's ``%run`` magic using ``<F5>``.

-------------------------------
IPython's object? Functionality
-------------------------------

If you're using gvim, mouse-over a variable to see IPython's ? equivalent. If
you're using vim from a terminal, or want to copy something from the
docstring, type ``<leader>d``. ``<leader>`` is usually ``\`` (the backslash
key).  This will open a quickpreview window, which can be closed by hitting
``q`` or ``<escape>``.

--------------------------------------
IPython's tab-completion Functionality
--------------------------------------
vim-ipython activates a 'completefunc' that queries IPython.
A completefunc is activated using ``Ctrl-X Ctrl-U`` in Insert Mode (vim
default). You can combine this functionality with SuperTab to get tab
completion 

---------------
Current issues:
---------------
For now, vim-ipython only connects to an ipython session in progress.

ipy.vim takes a while to load, I'll eventually move the python code to its
own file and do a lazy import (only when the IPython command is called)

The ipdb integration is not yet re-implemented.

Need to add more message handling for sub_channel messages from IPython
(i.e. notification of changes which were not sent from vim).

------
Thanks
------
@MinRK for guiding me through the IPython kernel manager protocol.
