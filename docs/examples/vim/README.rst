###########
vim-ipython
###########

A two-way integration between Vim and IPython 0.11+

* author: Paul Ivanov (http://pirsquared.org)
* github: http://github.com/ivanov/vim-ipython
* demos: http://pirsquared.org/vim-ipython/
* blogpost: http://pirsquared.org/blog/2011/07/28/vim-ipython/

Using this plugin, you can send lines or whole files for IPython to
execute, and also get back object introspection and word completions in
Vim, like what you get with: ``object?<enter>`` and ``object.<tab>`` in
IPython.

The big change from previous versions of ``ipy.vim`` is that it no longer
requires the old brittle ``ipy_vimserver.py`` instantiation, and since
it uses just vim and python, it is platform independent (i.e. should work
even on windows, unlike the previous \*nix only solution). The requirements
are IPython 0.11+ with zeromq capabilities, vim compiled with +python.

If you can launch ``ipython qtconsole`` or ``ipython kernel``, and
``:echo has('python')`` returns 1 in vim, you should be good to go.

-----------------
Quickstart Guide:
-----------------
Start ``ipython qtconsole`` [*]_ and copy the connection string.
Source ``ipy.vim`` file, which provides new IPython command::

  :source ipy.vim
  (or copy it to ~/.vim/ftplugin/python to load automatically)

  :IPythonClipboard
  (or :IPythonXSelection if you're using X11 without having to copy)

The :IPython command allows you to put the full connection string. For IPython
0.11, it would look like this::

  :IPython --existing --shell=41882 --iopub=43286 --stdin=34987 --hb=36697

and for IPython 0.12, like this::

  :IPython --existing kernel-85997.json

The ``:IPythonClipboard`` command just uses the ``+`` register to get the
connection string, whereas ``:IPythonXSelection`` uses the ``*`` register

.. [*] Though the demos above use ``qtconsole``, it is not required
    for this workflow, it's just that it was the easiest way to show how to
    make use of the new functionality in 0.11 release. In the current git
    trunk of IPython, you can use ``ipython kernel`` to create a kernel and
    get the connection string to use for any frontend (including vim-ipython).
    If you are still using 0.11, you can launch a regular kernel using
    ``python -c "from IPython.zmq.ipkernel import main; main()"``

------------------------
Sending lines to IPython
------------------------
Now type out a line and send it to IPython using ``<Ctrl-S>`` from Command mode::

  import os

You should see a notification message confirming the line was sent, along
with the input number for the line, like so ``In[1]: import os``.

``<Ctrl-S>`` also works from insert mode, but doesn't show notification,
unless ``monitor_subchannel`` is set to ``True`` (see `vim-ipython 'shell'`_,
below)

It also works blockwise in Visual Mode. Select and send these lines using
``<Ctrl-S>``::

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
completion.

-------------------
vim-ipython 'shell'
-------------------
**NEW since IPython 0.11**!

By monitoring km.sub_channel, we can recreate what messages were sent to
IPython, and what IPython sends back in response.

``monitor_subchannel`` is a parameter that sets whether this 'shell' should
updated on every sent command (default: True).

If at any later time you wish to bring this shell up, including if you've set
``monitor_subchannel=False``, hit ``<leader>s``.

-------
Options
-------
You can change these at the top of the ipy.vim::

  reselect = False            # reselect lines after sending from Visual mode
  show_execution_count = True # wait to get numbers for In[43]: feedback?
  monitor_subchannel = True   # update vim-ipython 'shell' on every send?
  run_flags= "-i"             # flags to for IPython's run magic when using <F5>

**Disabling default mappings**
In your own ``.vimrc``, if you don't like the mappings provided by default,
you can define a variable ``let g:ipy_perform_mappings=0`` which will prevent
vim-ipython from defining any of the default mappings.

---------------
Current issues:
---------------
- For now, vim-ipython only connects to an ipython session in progress.
- The ipdb integration is not yet re-implemented.
- If you're running inside ``screen``, read about the ``<CTRL-S>`` issue `here
  <http://munkymorgy.blogspot.com/2008/07/screen-ctrl-s-bug.html>`_, and add
  this line to your ``.bashrc`` to fix it::

    stty stop undef # to unmap ctrl-s

- In vim, if you're getting ``ImportError: No module named
  IPython.zmq.blockingkernelmanager`` but are able to import it in regular
  python, **either**

  1. your ``sys.path`` in vim differs from the ``sys.path`` in regular python.
     Try running these two lines, and comparing their output files::

      $ vim -c 'py import vim, sys; vim.current.buffer.append(sys.path)' -c ':wq vim_syspath'
      $ python -c "import sys; f=file('python_syspath','w'); f.write('\n'.join(sys.path)); f.close()"

  **or**

  2. your vim is compiled against a different python than you are launching. See
     if there's a difference between ::

      $ vim -c ':py import os; print os.__file__' -c ':q'
      $ python -c ':py import os; print os.__file__'

- For vim inside a terminal, using the arrow keys won't work inside a
  documentation buffer, because the mapping for ``<Esc>`` overlaps with
  ``^[OA`` and so on, and we use ``<Esc>`` as a quick way of closing the
  documentation preview window. If you want go without this quick close
  functionality and want to use the arrow keys instead, look for instructions
  starting with "Known issue: to enable the use of arrow keys..." in the
  ``get_doc_buffer`` function.

- @fholgado's update to ``minibufexpl.vim`` that is up on GitHub will always
  put the cursor in the minibuf after sending a command when
  ``monitor_subchannel`` is set. This is a bug in minibufexpl.vim and the workaround
  is described in vim-ipython issue #7.

----------------------------
Thanks and Bug Participation
----------------------------
* @MinRK for guiding me through the IPython kernel manager protocol.
* @nakamuray and @tcheneau for reporting and providing a fix for when vim is compiled without a gui (#1)
* @unpingco for reporting Windows bugs (#3,#4)
* @simon-b for terminal vim arrow key issue (#5)
* @jorgesca and @kwgoodman for shell (#6)
* @zeekay for easily allowing custom mappings (#9)
* @minrk for support of connection_file-based IPython connection (#13)
* @jorgesca for reporting the lack of profile handling capability (#14)
