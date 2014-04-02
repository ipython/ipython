.. _working_remotely:

Running a notebook server
=========================


The  :ref:`IPython notebook <htmlnotebook>` web-application is based on a
server-client structure.  This server uses a :ref:`two-process kernel
architecture <ipythonzmq>` based on ZeroMQ_, as well as Tornado_ for serving
HTTP requests. By default, a notebook server runs on http://127.0.0.1:8888/
and is accessible only from `localhost`. This document describes how you can
:ref:`secure a notebook server <notebook_server_security>` and how to :ref:`run it on
a public interface <notebook_public_server>`.

.. _ZeroMQ: http://zeromq.org

.. _Tornado: http://www.tornadoweb.org


.. _notebook_server_security:

Securing a notebook server
--------------------------

You can protect your notebook server with a simple single password by
setting the :attr:`NotebookApp.password` configurable. You can prepare a
hashed password using the function :func:`IPython.lib.security.passwd`:

.. sourcecode:: ipython

    In [1]: from IPython.lib import passwd
    In [2]: passwd()
    Enter password: 
    Verify password: 
    Out[2]: 'sha1:67c9e60bb8b6:9ffede0825894254b2e042ea597d771089e11aed'
    
.. note::

  :func:`~IPython.lib.security.passwd` can also take the password as a string
  argument. **Do not** pass it as an argument inside an IPython session, as it
  will be saved in your input history.

You can then add this to your :file:`ipython_notebook_config.py`, e.g.::

    # Password to use for web authentication
    c = get_config()
    c.NotebookApp.password = 
    u'sha1:67c9e60bb8b6:9ffede0825894254b2e042ea597d771089e11aed'

When using a password, it is a good idea to also use SSL, so that your 
password is not sent unencrypted by your browser. You can start the notebook 
to communicate via a secure protocol mode using a self-signed certificate with 
the command::

    $ ipython notebook --certfile=mycert.pem

.. note::

    A self-signed certificate can be generated with ``openssl``.  For example, 
    the following command will create a certificate valid for 365 days with 
    both the key and certificate data written to the same file::

        $ openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout mycert.pem -out mycert.pem

Your browser will warn you of a dangerous certificate because it is
self-signed.  If you want to have a fully compliant certificate that will not
raise warnings, it is possible (but rather involved) to obtain one,
as explained in detail in `this tutorial`__.

.. __: http://arstechnica.com/security/news/2009/12/how-to-get-set-with-a-secure-sertificate-for-free.ars
	
Keep in mind that when you enable SSL support, you will need to access the
notebook server over ``https://``, not over plain ``http://``.  The startup
message from the server prints this, but it is easy to overlook and think the
server is for some reason non-responsive.


.. _notebook_public_server:

Running a public notebook server
--------------------------------

If you want to access your notebook server remotely via a web browser,
you can do the following.  

Start by creating a certificate file and a hashed password, as explained 
above.  Then create a custom profile for the notebook, with the following 
command line, type::

  $ ipython profile create nbserver

In the profile directory just created, edit the file 
``ipython_notebook_config.py``.  By default, the file has all fields 
commented; the minimum set you need to uncomment and edit is the following::

     c = get_config()

     # Kernel config
     c.IPKernelApp.pylab = 'inline'  # if you want plotting support always

     # Notebook config
     c.NotebookApp.certfile = u'/absolute/path/to/your/certificate/mycert.pem'
     c.NotebookApp.ip = '*'
     c.NotebookApp.open_browser = False
     c.NotebookApp.password = u'sha1:bcd259ccf...[your hashed password here]'
     # It is a good idea to put it on a known, fixed port
     c.NotebookApp.port = 9999

You can then start the notebook and access it later by pointing your browser 
to ``https://your.host.com:9999`` with ``ipython notebook 
--profile=nbserver``.

Running with a different URL prefix
-----------------------------------

The notebook dashboard (the landing page with an overview
of the notebooks in your working directory) typically lives at the URL
``http://localhost:8888/``. If you prefer that it lives, together with the 
rest of the notebook, under a sub-directory,
e.g. ``http://localhost:8888/ipython/``, you can do so with
configuration options like the following (see above for instructions about
modifying ``ipython_notebook_config.py``)::

    c.NotebookApp.base_url = '/ipython/'
    c.NotebookApp.webapp_settings = {'static_url_prefix':'/ipython/static/'}

Using a different notebook store
--------------------------------

By default, the notebook server stores the notebook documents that it saves as 
files in the working directory of the notebook server, also known as the
``notebook_dir``. This  logic is implemented in the 
:class:`FileNotebookManager` class. However, the server can be configured to 
use a different notebook manager class, which can 
store the notebooks in a different format. 

The bookstore_ package currently allows users to store notebooks on Rackspace
CloudFiles or OpenStack Swift based object stores.

Writing a notebook manager is as simple as extending the base class
:class:`NotebookManager`. The simple_notebook_manager_ provides a great example
of an in memory notebook manager, created solely for the purpose of
illustrating the notebook manager API.

.. _bookstore: https://github.com/rgbkrk/bookstore

.. _simple_notebook_manager: https://github.com/khinsen/simple_notebook_manager

Known issues
------------

When behind a proxy, especially if your system or browser is set to autodetect
the proxy, the notebook web application might fail to connect to the server's
websockets, and present you with a warning at startup. In this case, you need
to configure your system not to use the proxy for the server's address.

For example, in Firefox, go to the Preferences panel, Advanced section,
Network tab, click 'Settings...', and add the address of the notebook server
to the 'No proxy for' field.
