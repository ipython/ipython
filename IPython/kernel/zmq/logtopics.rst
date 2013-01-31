=======================
Log Topic Specification
=======================

we use pyzmq to broadcast log events over a PUB socket. Engines, Controllers, etc. can all
broadcast. SUB sockets can be used to view the logs, and ZMQ topics are used to help
select out what to follow.

the PUBHandler object that emits the logs can ascribe topics to log messages. The order is:

<root_topic>.<loglevel>.<subtopic>[.<etc>]

root_topic is specified as an attribute
