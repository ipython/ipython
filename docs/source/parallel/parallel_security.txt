.. _parallelsecurity:

===========================
Security details of IPython
===========================

.. note::

    This section is not thorough, and IPython.kernel.zmq needs a thorough security
    audit.

IPython's :mod:`IPython.kernel.zmq` package exposes the full power of the
Python interpreter over a TCP/IP network for the purposes of parallel
computing. This feature brings up the important question of IPython's security
model. This document gives details about this model and how it is implemented
in IPython's architecture.

Process and network topology
============================

To enable parallel computing, IPython has a number of different processes that
run. These processes are discussed at length in the IPython documentation and
are summarized here:

* The IPython *engine*.  This process is a full blown Python
  interpreter in which user code is executed.  Multiple
  engines are started to make parallel computing possible.
* The IPython *hub*.  This process monitors a set of 
  engines and schedulers, and keeps track of the state of the processes. It listens
  for registration connections from engines and clients, and monitor connections
  from schedulers.
* The IPython *schedulers*. This is a set of processes that relay commands and results
  between clients and engines. They are typically on the same machine as the controller,
  and listen for connections from engines and clients, but connect to the Hub.
* The IPython *client*.  This process is typically an
  interactive Python process that is used to coordinate the
  engines to get a parallel computation done.

Collectively, these processes are called the IPython *cluster*, and the hub and schedulers
together are referred to as the *controller*.


These processes communicate over any transport supported by ZeroMQ (tcp,pgm,infiniband,ipc)
with a well defined topology. The IPython hub and schedulers listen on sockets. Upon
starting, an engine connects to a hub and registers itself, which then informs the engine
of the connection information for the schedulers, and the engine then connects to the
schedulers. These engine/hub and engine/scheduler connections persist for the
lifetime of each engine.

The IPython client also connects to the controller processes using a number of socket
connections. As of writing, this is one socket per scheduler (4), and 3 connections to the
hub for a total of 7. These connections persist for the lifetime of the client only.

A given IPython controller and set of engines engines typically has a relatively
short lifetime. Typically this lifetime corresponds to the duration of a single parallel
simulation performed by a single user. Finally, the hub, schedulers, engines, and client
processes typically execute with the permissions of that same user. More specifically, the
controller and engines are *not* executed as root or with any other superuser permissions.

Application logic
=================

When running the IPython kernel to perform a parallel computation, a user
utilizes the IPython client to send Python commands and data through the
IPython schedulers to the IPython engines, where those commands are executed
and the data processed. The design of IPython ensures that the client is the
only access point for the capabilities of the engines. That is, the only way
of addressing the engines is through a client.

A user can utilize the client to instruct the IPython engines to execute
arbitrary Python commands. These Python commands can include calls to the
system shell, access the filesystem, etc., as required by the user's
application code. From this perspective, when a user runs an IPython engine on
a host, that engine has the same capabilities and permissions as the user
themselves (as if they were logged onto the engine's host with a terminal).

Secure network connections
==========================

Overview
--------

ZeroMQ provides exactly no security. For this reason, users of IPython must be very
careful in managing connections, because an open TCP/IP socket presents access to
arbitrary execution as the user on the engine machines. As a result, the default behavior
of controller processes is to only listen for clients on the loopback interface, and the
client must establish SSH tunnels to connect to the controller processes.

.. warning:: 

    If the controller's loopback interface is untrusted, then IPython should be considered
    vulnerable, and this extends to the loopback of all connected clients, which have
    opened a loopback port that is redirected to the controller's loopback port.


SSH
---

Since ZeroMQ provides no security, SSH tunnels are the primary source of secure
connections. A connector file, such as `ipcontroller-client.json`, will contain
information for connecting to the controller, possibly including the address of an
ssh-server through with the client is to tunnel. The Client object then creates tunnels
using either [OpenSSH]_ or [Paramiko]_, depending on the platform. If users do not wish to
use OpenSSH or Paramiko, or the tunneling utilities are insufficient, then they may
construct the tunnels themselves, and simply connect clients and engines as if the
controller were on loopback on the connecting machine.


Authentication
--------------

To protect users of shared machines, [HMAC]_ digests are used to sign messages, using a
shared key.

The Session object that handles the message protocol uses a unique key to verify valid
messages. This can be any value specified by the user, but the default behavior is a
pseudo-random 128-bit number, as generated by `uuid.uuid4()`. This key is used to
initialize an HMAC object, which digests all messages, and includes that digest as a
signature and part of the message. Every message that is unpacked (on Controller, Engine,
and Client) will also be digested by the receiver, ensuring that the sender's key is the
same as the receiver's. No messages that do not contain this key are acted upon in any
way. The key itself is never sent over the network.

There is exactly one shared key per cluster - it must be the same everywhere. Typically,
the controller creates this key, and stores it in the private connection files
`ipython-{engine|client}.json`. These files are typically stored in the
`~/.ipython/profile_<name>/security` directory, and are maintained as readable only by the
owner, just as is common practice with a user's keys in their `.ssh` directory.

.. warning::

    It is important to note that the signatures protect against unauthorized messages,
    but, as there is no encryption, provide exactly no protection of data privacy.  It is
    possible, however, to use a custom serialization scheme (via Session.packer/unpacker
    traits) that does incorporate your own encryption scheme.



Specific security vulnerabilities
=================================

There are a number of potential security vulnerabilities present in IPython's
architecture. In this section we discuss those vulnerabilities and detail how
the security architecture described above prevents them from being exploited.

Unauthorized clients
--------------------

The IPython client can instruct the IPython engines to execute arbitrary
Python code with the permissions of the user who started the engines. If an
attacker were able to connect their own hostile IPython client to the IPython
controller, they could instruct the engines to execute code.


On the first level, this attack is prevented by requiring access to the controller's
ports, which are recommended to only be open on loopback if the controller is on an
untrusted local network. If the attacker does have access to the Controller's ports, then
the attack is prevented by the capabilities based client authentication of the execution
key. The relevant authentication information is encoded into the JSON file that clients
must present to gain access to the IPython controller. By limiting the distribution of
those keys, a user can grant access to only authorized persons, just as with SSH keys.

It is highly unlikely that an execution key could be guessed by an attacker
in a brute force guessing attack. A given instance of the IPython controller
only runs for a relatively short amount of time (on the order of hours). Thus
an attacker would have only a limited amount of time to test a search space of
size 2**128.  For added security, users can have arbitrarily long keys.

.. warning::

    If the attacker has gained enough access to intercept loopback connections on *either* the
    controller or client, then a duplicate message can be sent. To protect against this,
    recipients only allow each signature once, and consider duplicates invalid.  However,
    the duplicate message could be sent to *another* recipient using the same key,
    and it would be considered valid.


Unauthorized engines
--------------------

If an attacker were able to connect a hostile engine to a user's controller,
the user might unknowingly send sensitive code or data to the hostile engine.
This attacker's engine would then have full access to that code and data.

This type of attack is prevented in the same way as the unauthorized client
attack, through the usage of the capabilities based authentication scheme.

Unauthorized controllers
------------------------

It is also possible that an attacker could try to convince a user's IPython
client or engine to connect to a hostile IPython controller. That controller
would then have full access to the code and data sent between the IPython
client and the IPython engines.

Again, this attack is prevented through the capabilities in a connection file, which
ensure that a client or engine connects to the correct controller. It is also important to
note that the connection files also encode the IP address and port that the controller is
listening on, so there is little chance of mistakenly connecting to a controller running
on a different IP address and port.

When starting an engine or client, a user must specify the key to use
for that connection. Thus, in order to introduce a hostile controller, the
attacker must convince the user to use the key associated with the
hostile controller. As long as a user is diligent in only using keys from
trusted sources, this attack is not possible.

.. note::

    I may be wrong, the unauthorized controller may be easier to fake than this.

Other security measures
=======================

A number of other measures are taken to further limit the security risks
involved in running the IPython kernel.

First, by default, the IPython controller listens on random port numbers.
While this can be overridden by the user, in the default configuration, an
attacker would have to do a port scan to even find a controller to attack.
When coupled with the relatively short running time of a typical controller
(on the order of hours), an attacker would have to work extremely hard and
extremely *fast* to even find a running controller to attack.

Second, much of the time, especially when run on supercomputers or clusters,
the controller is running behind a firewall. Thus, for engines or client to
connect to the controller:

* The different processes have to all be behind the firewall.

or:

* The user has to use SSH port forwarding to tunnel the
  connections through the firewall.
   
In either case, an attacker is presented with additional barriers that prevent
attacking or even probing the system.

Summary
=======

IPython's architecture has been carefully designed with security in mind. The
capabilities based authentication model, in conjunction with SSH tunneled
TCP/IP channels, address the core potential vulnerabilities in the system,
while still enabling user's to use the system in open networks.

.. [RFC5246] <http://tools.ietf.org/html/rfc5246>

.. [OpenSSH] <http://www.openssh.com/>
.. [Paramiko] <http://www.lag.net/paramiko/>
.. [HMAC] <http://tools.ietf.org/html/rfc2104.html>
