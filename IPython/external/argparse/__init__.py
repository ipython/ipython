try:
    import argparse
    # Workaround an argparse bug, FIXED in argparse 1.1.0
    if 'RawTextHelpFormatterArgumentDefaultsHelpFormatter' in argparse.__all__:
        import itertools
        argparse.__all__ = list(itertools.chain( [i for i in argparse.__all__
            if i != 'RawTextHelpFormatterArgumentDefaultsHelpFormatter'],
            ['RawTextHelpFormatter', 'ArgumentDefaultsHelpFormatter']))
    argparse.__all__.append('SUPPRESS')
    from argparse import *
except ImportError:
    from _argparse import *
    from _argparse import SUPPRESS
