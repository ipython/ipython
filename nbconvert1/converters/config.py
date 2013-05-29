from IPython.utils.traitlets import (Unicode, List, Bool)
from IPython.config.configurable import Configurable

class GlobalConfigurable(Configurable):
    """Global configurable class for shared config

    Usefull for display data priority that might be use by many trasnformers
    """

    display_data_priority = List(['html', 'pdf', 'svg', 'latex', 'png', 'jpg', 'jpeg' , 'text'],
            config=True,
              help= """
                    An ordered list of prefered output type, the first
                    encounterd will usually be used when converting discarding
                    the others.
                    """
            )

    def __init__(self, config=None, **kw):
        super(GlobalConfigurable, self).__init__( config=config, **kw)
