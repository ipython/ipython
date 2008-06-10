from IPython.config.api import *

class SubSubSample(Config):
    my_int = Int(3)


class Sample(Config):
    my_float = Float(3)
    my_choice = Enum('a','b','c')

    class MiddleSection(Config):
        left_alone = Enum('1','2','c')
        unknown_mod = Module('asd')

    class SubSample(Config):
        subsample_uri = URI('http://localhost:8080')

        # Example of how to include external config
        SubSubSample = SubSubSample()
