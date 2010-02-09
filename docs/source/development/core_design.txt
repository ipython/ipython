========================================
 Design proposal for mod:`IPython.core`
========================================

Currently mod:`IPython.core` is not well suited for use in GUI
applications. The purpose of this document is to describe a design that will
resolve this limitation.

Process and thread model
========================

The design described here is based on a two process model. These two processes
are:

1. The IPython engine/kernel. This process contains the user's namespace and is
   responsible for executing user code. If user code uses
   :mod:`enthought.traits` or uses a GUI toolkit to perform plotting, the GUI
   event loop will run in this process.

2. The GUI application. The user facing GUI application will run in a second
   process that communicates directly with the IPython engine using a suitable
   RPC mechanism. The GUI application will not execute any user code. The
   canonical example of a GUI application that talks to the IPython engine,
   would be a GUI based IPython terminal. However, the GUI application could
   provide a more sophisticated interface such as a notebook.

We now describe the treading model of the IPython engine.  Two threads will be
used to implement the IPython engine: a main thread that executes user code and
a networking thread that communicates with the outside world. This specific
design is required by a number of different factors.

First, The IPython engine must run the GUI event loop if the user wants to
perform interactive plotting. Because of the design of most GUIs, this means
that the user code (which will make GUI calls) must live in the main thread.

Second, networking code in the engine (Twisted or otherwise) must be able to
communicate with the outside world while user code runs. An example would be if
user code does the following::

    import time
    for i in range(10):
        print i
        time.sleep(2)

We would like to result of each ``print i`` to be seen by the GUI application
before the entire code block completes. We call this asynchronous printing.
For this to be possible, the networking code has to be able to be able to
communicate the value of ``stdout`` to the GUI application while user code is
run. Another example is using :mod:`IPython.kernel.client` in user code to
perform a parallel computation by talking to an IPython controller and a set of
engines (these engines are separate from the one we are discussing here). This
module requires the Twisted event loop to be run in a different thread than
user code.

For the GUI application, threads are optional. However, the GUI application
does need to be able to perform network communications asynchronously (without
blocking the GUI itself). With this in mind, there are two options:

* Use Twisted (or another non-blocking socket library) in the same thread as
  the GUI event loop.

* Don't use Twisted, but instead run networking code in the GUI application
  using blocking sockets in threads. This would require the usage of polling
  and queues to manage the networking in the GUI application.

Thus, for the GUI application, there is a choice between non-blocking sockets
(Twisted) or threads.

Interprocess communication
==========================

The GUI application will use interprocess communication (IPC) to communicate
with the networking thread of the engine. Because this communication will
typically happen over localhost, a simple, one way, non-secure protocol like
XML-RPC or JSON-RPC can be used. These options will also make it easy to
implement the required networking in the GUI application using the standard
library. In applications where secure communications are required, Twisted and
Foolscap will probably be the best way to go for now.

Using this communication channel, the GUI application will be able to perform
the following actions with the engine:

* Pass code (as a string) to be executed by the engine in the user's namespace
  as a string.

* Get the current value of stdout and stderr.

* Pass a string to the engine to be completed when the GUI application
  receives a tab completion event.

* Get a list of all variable names in the user's namespace.

* Other similar actions.

Engine details
==============

As discussed above, the engine will consist of two threads: a main thread and a
networking thread. These two threads will communicate using a pair of queues:
one for data and requests passing to the main thread (the main thread's "input
queue") and another for data and requests passing out of the main thread (the
main thread's "output queue"). Both threads will have an event loop that will
enqueue elements on one queue and dequeue elements on the other queue.

The event loop of the main thread will be of a different nature depending on if
the user wants to perform interactive plotting. If they do want to perform
interactive plotting, the main threads event loop will simply be the GUI event
loop. In that case, GUI timers will be used to monitor the main threads input
queue. When elements appear on that queue, the main thread will respond
appropriately. For example, if the queue contains an element that consists of
user code to execute, the main thread will call the appropriate method of its
IPython instance. If the user does not want to perform interactive plotting,
the main thread will have a simpler event loop that will simply block on the
input queue. When something appears on that queue, the main thread will awake
and handle the request.

The event loop of the networking thread will typically be the Twisted event
loop.  While it is possible to implement the engine's networking without using
Twisted, at this point, Twisted provides the best solution. Note that the GUI
application does not need to use Twisted in this case. The Twisted event loop
will contain an XML-RPC or JSON-RPC server that takes requests over the network
and handles those requests by enqueing elements on the main thread's input
queue or dequeing elements on the main thread's output queue.

Because of the asynchronous nature of the network communication, a single input
and output queue will be used to handle the interaction with the main
thread. It is also possible to use multiple queues to isolate the different
types of requests, but our feeling is that this is more complicated than it
needs to be.

One of the main issues is how stdout/stderr will be handled. Our idea is to
replace sys.stdout/sys.stderr by custom classes that will immediately write
data to the main thread's output queue when user code writes to these streams
(by doing print). Once on the main thread's output queue, the networking thread
will make the data available to the GUI application over the network.

One unavoidable limitation in this design is that if user code does a print and
then enters non-GIL-releasing extension code, the networking thread will go
silent until the GIL is again released. During this time, the networking thread
will not be able to process the GUI application's requests of the engine. Thus,
the values of stdout/stderr will be unavailable during this time. This goes
beyond stdout/stderr, however.  Anytime the main thread is holding the GIL, the
networking thread will go silent and be unable to handle requests.

Refactoring of IPython.core
===========================

We need to go through IPython.core and describe what specifically needs to be
done.
