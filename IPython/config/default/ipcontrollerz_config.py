from IPython.config.loader import Config

c = get_config()

#-----------------------------------------------------------------------------
# Global configuration
#-----------------------------------------------------------------------------

# Basic Global config attributes

# Start up messages are logged to stdout using the logging module.
# These all happen before the twisted reactor is started and are
# useful for debugging purposes. Can be (10=DEBUG,20=INFO,30=WARN,40=CRITICAL) 
# and smaller is more verbose.
# c.Global.log_level = 20

# Log to a file in cluster_dir/log, otherwise just log to sys.stdout.
# c.Global.log_to_file = False

# Remove old logs from cluster_dir/log before starting.
# c.Global.clean_logs = True

# A list of Python statements that will be run before starting the 
# controller. This is provided because occasionally certain things need to 
# be imported in the controller for pickling to work.
# c.Global.import_statements = ['import math']

# Reuse the controller's JSON files. If False, JSON files are regenerated
# each time the controller is run. If True, they will be reused, *but*, you
# also must set the network ports by hand. If set, this will override the
# values set for the client and engine connections below.
# c.Global.reuse_files = True

# Enable exec_key authentication on all messages. Default is True
# c.Global.secure = True

# The working directory for the process. The application will use os.chdir
# to change to this directory before starting.
# c.Global.work_dir = os.getcwd()

# The log url for logging to an `iploggerz` application.  This will override
# log-to-file.
# c.Global.log_url = 'tcp://127.0.0.1:20202'

# The specific external IP that is used to disambiguate multi-interface URLs.
# The default behavior is to guess from external IPs gleaned from `socket`.
# c.Global.location = '192.168.1.123'

# The ssh server remote clients should use to connect to this controller.
# It must be a machine that can see the interface specified in client_ip.
# The default for client_ip is localhost, in which case the sshserver must
# be an external IP of the controller machine.
# c.Global.sshserver = 'controller.example.com'

# the url to use for registration.  If set, this overrides engine-ip,
# engine-transport client-ip,client-transport, and regport.
# c.RegistrationFactory.url = 'tcp://*:12345'

# the port to use for registration.  Clients and Engines both use this
# port for registration.
# c.RegistrationFactory.regport = 10101

#-----------------------------------------------------------------------------
# Configure the Task Scheduler
#-----------------------------------------------------------------------------

# The routing scheme. 'pure' will use the pure-ZMQ scheduler. Any other 
# value will use a Python scheduler with various routing schemes.
# python schemes are: lru, weighted, random, twobin. Default is 'weighted'.
# Note that the pure ZMQ scheduler does not support many features, such as
# dying engines, dependencies, or engine-subset load-balancing.
# c.ControllerFactory.scheme = 'pure'

# The pure ZMQ scheduler can limit the number of outstanding tasks per engine
# by using the ZMQ HWM option.  This allows engines with long-running tasks
# to not steal too many tasks from other engines. The default is 0, which
# means agressively distribute messages, never waiting for them to finish.
# c.ControllerFactory.hwm = 1

# Whether to use Threads or Processes to start the Schedulers.  Threads will
# use less resources, but potentially reduce throughput. Default is to 
# use processes.  Note that the a Python scheduler will always be in a Process.
# c.ControllerFactory.usethreads

#-----------------------------------------------------------------------------
# Configure the Hub
#-----------------------------------------------------------------------------

# Which class to use for the db backend.  Currently supported are DictDB (the
# default), and MongoDB. Uncomment this line to enable MongoDB, which will
# slow-down the Hub's responsiveness, but also reduce its memory footprint.
# c.HubFactory.db_class = 'IPython.parallel.mongodb.MongoDB'

# The heartbeat ping frequency.  This is the frequency (in ms) at which the
# Hub pings engines for heartbeats.  This determines how quickly the Hub
# will react to engines coming and going.  A lower number means faster response
# time, but more network activity.  The default is 100ms
# c.HubFactory.ping = 100

# HubFactory queue port pairs, to set by name: mux, iopub, control, task.  Set
# each as a tuple of length 2 of ints.  The default is to find random
# available ports
# c.HubFactory.mux = (10102,10112)

#-----------------------------------------------------------------------------
# Configure the client connections
#-----------------------------------------------------------------------------

# Basic client connection config attributes

# The network interface the controller will listen on for client connections.
# This should be an IP address or interface on the controller. An asterisk
# means listen on all interfaces. The transport can be any transport
# supported by zeromq (tcp,epgm,pgm,ib,ipc):
# c.HubFactory.client_ip = '*'
# c.HubFactory.client_transport = 'tcp'

# individual client ports to configure by name: query_port, notifier_port
# c.HubFactory.query_port = 12345

#-----------------------------------------------------------------------------
# Configure the engine connections
#-----------------------------------------------------------------------------

# Basic config attributes for the engine connections.

# The network interface the controller will listen on for engine connections.
# This should be an IP address or interface on the controller. An asterisk
# means listen on all interfaces. The transport can be any transport
# supported by zeromq (tcp,epgm,pgm,ib,ipc):
# c.HubFactory.engine_ip = '*'
# c.HubFactory.engine_transport = 'tcp'

# set the engine heartbeat ports to use:
# c.HubFactory.hb = (10303,10313)

#-----------------------------------------------------------------------------
# Configure the TaskRecord database backend
#-----------------------------------------------------------------------------

# For memory/persistance reasons, tasks can be stored out-of-memory in a database.
# Currently, only sqlite and mongodb are supported as backends, but the interface
# is fairly simple, so advanced developers could write their own backend.

# ----- in-memory configuration --------
# this line restores the default behavior: in-memory storage of all results.
# c.HubFactory.db_class = 'IPython.parallel.dictdb.DictDB'

# ----- sqlite configuration --------
# use this line to activate sqlite:
# c.HubFactory.db_class = 'IPython.parallel.sqlitedb.SQLiteDB'

# You can specify the name of the db-file.  By default, this will be located
# in the active cluster_dir, e.g. ~/.ipython/clusterz_default/tasks.db
# c.SQLiteDB.filename = 'tasks.db'

# You can also specify the location of the db-file, if you want it to be somewhere
# other than the cluster_dir.
# c.SQLiteDB.location = '/scratch/'

# This will specify the name of the table for the controller to use.  The default
# behavior is to use the session ID of the SessionFactory object (a uuid). Overriding
# this will result in results persisting for multiple sessions.
# c.SQLiteDB.table = 'results'

# ----- mongodb configuration --------
# use this line to activate mongodb:
# c.HubFactory.db_class = 'IPython.parallel.mongodb.MongoDB'

# You can specify the args and kwargs pymongo will use when creating the Connection.
# For more information on what these options might be, see pymongo documentation.
# c.MongoDB.connection_kwargs = {}
# c.MongoDB.connection_args = []

# This will specify the name of the mongo database for the controller to use.  The default
# behavior is to use the session ID of the SessionFactory object (a uuid). Overriding
# this will result in task results persisting through multiple sessions.
# c.MongoDB.database = 'ipythondb'


