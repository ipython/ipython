"""This should be run directly from ipython, and it should NOT crash.

It can't currently be run via runtests b/c exception handling changes there,
and this is precisely testing exception handling problems."""

ipmagic('xmode verbose')

src = """
class suck(object):
    def __repr__(self):
        raise ValueError("who needs repr anyway")

suck()
"""

__IPYTHON__.runlines(src)
