"""A simple example of how to use IPython.config.application.Application.

This should serve as a simple example that shows how the IPython config
system works. The main classes are:

* IPython.config.configurable.Configurable
* IPython.config.configurable.SingletonConfigurable
* IPython.config.loader.Config
* IPython.config.application.Application

To see the command line option help, run this program from the command line::

    $ python appconfig.py -h

To make one of your classes configurable (from the command line and config
files) inherit from Configurable and declare class attributes as traits (see
classes Foo and Bar below). To make the traits configurable, you will need
to set the following options:

* ``config``: set to ``True`` to make the attribute configurable.
* ``shortname``: by default, configurable attributes are set using the syntax
  "Classname.attributename". At the command line, this is a bit verbose, so
  we allow "shortnames" to be declared. Setting a shortname is optional, but
  when you do this, you can set the option at the command line using the
  syntax: "shortname=value".
* ``help``: set the help string to display a help message when the ``-h``
  option is given at the command line. The help string should be valid ReST.

When the config attribute of an Application is updated, it will fire all of
the trait's events for all of the config=True attributes.
"""

import sys

from IPython.config.configurable import Configurable
from IPython.config.application import Application
from IPython.utils.traitlets import (
    Bool, Unicode, Int, Float, List
)


class Foo(Configurable):
    """A class that has configurable, typed attributes.

    """

    i = Int(0, config=True, shortname='i', help="The integer i.")
    j = Int(1, config=True, shortname='j', help="The integer j.")
    name = Unicode(u'Brian', config=True, shortname='name', help="First name.")


class Bar(Configurable):

    enabled = Bool(True, config=True, shortname="enabled", help="Enable bar.")


class MyApp(Application):

    app_name = Unicode(u'myapp')
    running = Bool(False, config=True, shortname="running",
                   help="Is the app running?")
    classes = List([Bar, Foo])
    config_file = Unicode(u'', config=True, shortname="config_file",
                   help="Load this config file")
    
    shortnames = dict(i='Foo.i',j='Foo.j',name='Foo.name',
                        enabled='Bar.enabled')
    
    macros = dict(enable='Bar.enabled=True', disable='Bar.enabled=False')
    macro_help = dict(
            enable="""Set Bar.enabled to True""",
            disable="""Set Bar.enabled to False"""
    )

    def init_foo(self):
        # Pass config to other classes for them to inherit the config.
        self.foo = Foo(config=self.config)

    def init_bar(self):
        # Pass config to other classes for them to inherit the config.
        self.bar = Bar(config=self.config)



def main():
    app = MyApp()
    app.parse_command_line()
    if app.config_file:
        app.load_config_file(app.config_file)
    app.init_foo()
    app.init_bar()
    print "app.config:"
    print app.config


if __name__ == "__main__":
    main()
