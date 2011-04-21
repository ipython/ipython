import sys

from IPython.config.configurable import Configurable
from IPython.utils.traitlets import (
    Bool, Unicode, Int, Float, List
)
from IPython.config.loader import KeyValueConfigLoader

class Foo(Configurable):

    i = Int(0, config=True, shortname='i', help="The integer i.")
    j = Int(1, config=True, shortname='j', help="The integer j.")
    name = Unicode(u'Brian', config=True, shortname='name', help="First name.")


class Bar(Configurable):

    enabled = Bool(True, config=True, shortname="bar-enabled", help="Enable bar.")


class MyApp(Configurable):

    app_name = Unicode(u'myapp', config=True, shortname="myapp", help="The app name.")
    running = Bool(False, config=True, shortname="running", help="Is the app running?")
    classes = List([Bar, Foo])

    def __init__(self, **kwargs):
        Configurable.__init__(self, **kwargs)
        self.classes.insert(0, self.__class__)

    def print_help(self):
        for cls in self.classes:
            cls.class_print_help()
            print

    def parse_command_line(self, argv=None):
        if argv is None:
            argv = sys.argv[1:]
        if '-h' in argv or '--h' in argv:
            self.print_help()
            sys.exit(1)
        loader = KeyValueConfigLoader(argv=argv, classes=self.classes)
        config = loader.load_config()
        self.config = config


def main():
    app = MyApp()
    app.parse_command_line()
    print "app.config:"
    print app.config


if __name__ == "__main__":
    main()
