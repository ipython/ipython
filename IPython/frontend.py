import sys
import types


class ShimModule(types.ModuleType):

    def __getattribute__(self, key):
        exec 'from IPython import %s' % key
        return eval(key)

sys.modules['IPython.frontend'] = ShimModule('frontend')
