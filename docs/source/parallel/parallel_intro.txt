.. _parallel_overview:

============================
Overview and getting started
============================


Examples
========

We have various example scripts and notebooks for using IPython.parallel in our
:file:`docs/examples/parallel` directory, or they can be found `on GitHub`__.
Some of these are covered in more detail in the :ref:`examples
<parallel_examples>` section.

.. __: https://github.com/ipython/ipython/tree/master/docs/examples/parallel

Introduction
============

This section gives an overview of IPython's sophisticated and powerful
architecture for parallel and distributed computing. This architecture
abstracts out parallelism in a very general way, which enables IPython to
support many different styles of parallelism including:

* Single program, multiple data (SPMD) parallelism.
* Multiple program, multiple data (MPMD) parallelism.
* Message passing using MPI.
* Task farming.
* Data parallel.
* Combinations of these approaches.
* Custom user defined approaches.

Most importantly, IPython enables all types of parallel applications to
be developed, executed, debugged and monitored *interactively*. Hence,
the ``I`` in IPython.  The following are some example usage cases for IPython:

* Quickly parallelize algorithms that are embarrassingly parallel
  using a number of simple approaches.  Many simple things can be
  parallelized interactively in one or two lines of code.

* Steer traditional MPI applications on a supercomputer from an
  IPython session on your laptop.

* Analyze and visualize large datasets (that could be remote and/or
  distributed) interactively using IPython and tools like
  matplotlib/TVTK.

* Develop, test and debug new parallel algorithms 
  (that may use MPI) interactively.

* Tie together multiple MPI jobs running on different systems into
  one giant distributed and parallel system.

* Start a parallel job on your cluster and then have a remote 	
  collaborator connect to it and pull back data into their 
  local IPython session for plotting and analysis.

* Run a set of tasks on a set of CPUs using dynamic load balancing.

.. tip::

   At the SciPy 2011 conference in Austin, Min Ragan-Kelley presented a
   complete 4-hour tutorial on the use of these features, and all the materials
   for the tutorial are now `available online`__.  That tutorial provides an
   excellent, hands-on oriented complement to the reference documentation
   presented here.

.. __: http://minrk.github.com/scipy-tutorial-2011

Architecture overview
=====================

.. figure:: figs/wideView.png
    :width: 300px


The IPython architecture consists of four components:

* The IPython engine.
* The IPython hub.
* The IPython schedulers.
* The controller client.

These components live in the :mod:`IPython.parallel` package and are
installed with IPython.  They do, however, have additional dependencies
that must be installed.  For more information, see our
:ref:`installation documentation <install_index>`.

.. TODO: include zmq in install_index

IPython engine
---------------

The IPython engine is a Python instance that takes Python commands over a
network connection. Eventually, the IPython engine will be a full IPython
interpreter, but for now, it is a regular Python interpreter. The engine
can also handle incoming and outgoing Python objects sent over a network
connection.  When multiple engines are started, parallel and distributed
computing becomes possible. An important feature of an IPython engine is
that it blocks while user code is being executed. Read on for how the
IPython controller solves this problem to expose a clean asynchronous API
to the user.

IPython controller
------------------

The IPython controller processes provide an interface for working with a set of engines.
At a general level, the controller is a collection of processes to which IPython engines
and clients can connect. The controller is composed of a :class:`Hub` and a collection of
:class:`Schedulers`. These Schedulers are typically run in separate processes but on the
same machine as the Hub, but can be run anywhere from local threads or on remote machines.

The controller also provides a single point of contact for users who wish to
utilize the engines connected to the controller. There are different ways of
working with a controller. In IPython, all of these models are implemented via
the :meth:`.View.apply` method, after
constructing :class:`.View` objects to represent subsets of engines. The two
primary models for interacting with engines are:

* A **Direct** interface, where engines are addressed explicitly.
* A **LoadBalanced** interface, where the Scheduler is trusted with assigning work to
  appropriate engines.

Advanced users can readily extend the View models to enable other
styles of parallelism. 

.. note:: 

    A single controller and set of engines can be used with multiple models
    simultaneously. This opens the door for lots of interesting things.


The Hub
*******

The center of an IPython cluster is the Hub. This is the process that keeps
track of engine connections, schedulers, clients, as well as all task requests and
results. The primary role of the Hub is to facilitate queries of the cluster state, and
minimize the necessary information required to establish the many connections involved in
connecting new clients and engines.


Schedulers
**********

All actions that can be performed on the engine go through a Scheduler. While the engines
themselves block when user code is run, the schedulers hide that from the user to provide
a fully asynchronous interface to a set of engines.


IPython client and views
------------------------

There is one primary object, the :class:`~.parallel.Client`, for connecting to a cluster.
For each execution model, there is a corresponding :class:`~.parallel.View`. These views
allow users to interact with a set of engines through the interface. Here are the two default
views:

* The :class:`DirectView` class for explicit addressing.
* The :class:`LoadBalancedView` class for destination-agnostic scheduling.

Security
--------

IPython uses ZeroMQ for networking, which has provided many advantages, but
one of the setbacks is its utter lack of security [ZeroMQ]_. By default, no IPython
connections are encrypted, but open ports only listen on localhost. The only
source of security for IPython is via ssh-tunnel. IPython supports both shell
(`openssh`) and `paramiko` based tunnels for connections.  There is a key necessary
to submit requests, but due to the lack of encryption, it does not provide
significant security if loopback traffic is compromised.

In our architecture, the controller is the only process that listens on
network ports, and is thus the main point of vulnerability. The standard model
for secure connections is to designate that the controller listen on
localhost, and use ssh-tunnels to connect clients and/or
engines.

To connect and authenticate to the controller an engine or client needs
some information that the controller has stored in a JSON file.
Thus, the JSON files need to be copied to a location where
the clients and engines can find them. Typically, this is the
:file:`~/.ipython/profile_default/security` directory on the host where the 
client/engine is running (which could be a different host than the controller). 
Once the JSON files are copied over, everything should work fine.

Currently, there are two JSON files that the controller creates:

ipcontroller-engine.json
    This JSON file has the information necessary for an engine to connect
    to a controller.

ipcontroller-client.json
    The client's connection information.  This may not differ from the engine's,
    but since the controller may listen on different ports for clients and
    engines, it is stored separately.

ipcontroller-client.json will look something like this, under default localhost
circumstances:

.. sourcecode:: python

    {
      "url":"tcp:\/\/127.0.0.1:54424",
      "exec_key":"a361fe89-92fc-4762-9767-e2f0a05e3130",
      "ssh":"",
      "location":"10.19.1.135"
    }

If, however, you are running the controller on a work node on a cluster, you will likely
need to use ssh tunnels to connect clients from your laptop to it.  You will also
probably need to instruct the controller to listen for engines coming from other work nodes
on the cluster.  An example of ipcontroller-client.json, as created by::

    $> ipcontroller --ip=* --ssh=login.mycluster.com


.. sourcecode:: python

    {
      "url":"tcp:\/\/*:54424",
      "exec_key":"a361fe89-92fc-4762-9767-e2f0a05e3130",
      "ssh":"login.mycluster.com",
      "location":"10.0.0.2"
    }
More details of how these JSON files are used are given below.

A detailed description of the security model and its implementation in IPython
can be found :ref:`here <parallelsecurity>`.

.. warning::

    Even at its most secure, the Controller listens on ports on localhost, and
    every time you make a tunnel, you open a localhost port on the connecting
    machine that points to the Controller. If localhost on the Controller's
    machine, or the machine of any client or engine, is untrusted, then your
    Controller is insecure. There is no way around this with ZeroMQ.



Getting Started
===============

To use IPython for parallel computing, you need to start one instance of the
controller and one or more instances of the engine. Initially, it is best to
simply start a controller and engines on a single host using the
:command:`ipcluster` command. To start a controller and 4 engines on your
localhost, just do::

    $ ipcluster start -n 4

More details about starting the IPython controller and engines can be found
:ref:`here <parallel_process>`

Once you have started the IPython controller and one or more engines, you
are ready to use the engines to do something useful. To make sure
everything is working correctly, try the following commands:

.. sourcecode:: ipython

	In [1]: from IPython.parallel import Client
	
	In [2]: c = Client()
	
	In [4]: c.ids
	Out[4]: set([0, 1, 2, 3])
	
	In [5]: c[:].apply_sync(lambda : "Hello, World")
	Out[5]: [ 'Hello, World', 'Hello, World', 'Hello, World', 'Hello, World' ]


When a client is created with no arguments, the client tries to find the corresponding JSON file
in the local `~/.ipython/profile_default/security` directory. Or if you specified a profile,
you can use that with the Client.  This should cover most cases:

.. sourcecode:: ipython

    In [2]: c = Client(profile='myprofile')

If you have put the JSON file in a different location or it has a different name, create the
client like this:

.. sourcecode:: ipython

    In [2]: c = Client('/path/to/my/ipcontroller-client.json')

Remember, a client needs to be able to see the Hub's ports to connect. So if they are on a
different machine, you may need to use an ssh server to tunnel access to that machine,
then you would connect to it with:

.. sourcecode:: ipython

    In [2]: c = Client('/path/to/my/ipcontroller-client.json', sshserver='me@myhub.example.com')

Where 'myhub.example.com' is the url or IP address of the machine on
which the Hub process is running (or another machine that has direct access to the Hub's ports).

The SSH server may already be specified in ipcontroller-client.json, if the controller was
instructed at its launch time.

You are now ready to learn more about the :ref:`Direct
<parallel_multiengine>` and :ref:`LoadBalanced <parallel_task>` interfaces to the
controller.

.. [ZeroMQ] ZeroMQ.  http://www.zeromq.org
