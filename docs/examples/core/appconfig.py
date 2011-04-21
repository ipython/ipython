import sys

from IPython.config.configurable import Configurable
from IPython.config.application import Application
from IPython.utils.traitlets import (
    Bool, Unicode, Int, Float, List
)

class Foo(Configurable):

    i = Int(0, config=True, shortname='i', help="The integer i.")
    j = Int(1, config=True, shortname='j', help="The integer j.")
    name = Unicode(u'Brian', config=True, shortname='name', help="First name.")


class Bar(Configurable):

    enabled = Bool(True, config=True, shortname="bar-enabled", help="Enable bar.")


class MyApp(Application):

    app_name = Unicode(u'myapp')
    running = Bool(False, config=True, shortname="running", help="Is the app running?")
    classes = List([Bar, Foo])
    config_file = Unicode(u'', config=True, shortname="config-file", help="Load this config file")


def main():
    app = MyApp()
    app.parse_command_line()
    if app.config_file:
        app.load_config_file(app.config_file)
    print "app.config:"
    print app.config


if __name__ == "__main__":
    main()
