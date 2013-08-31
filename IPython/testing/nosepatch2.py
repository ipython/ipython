from nose.plugins.attrib import AttributeSelector

# Workaround for nose issue #728, to allow our parametric tests to run
# in Python 2.
# https://github.com/nose-devs/nose/issues/728
# This is required with nose 1.3.0, the current version at the time of
# writing.

# This patch precludes setting nose attributes on a @staticmethod test. We
# don't currently use nose attributes, but a more sophisticated solution
# can be devised if we decide to.

def wantMethod(self, method):
    """Accept the method if its attributes match.
    """
    try:
        cls = method.im_class
    except AttributeError:
        # Monkeypatch: return None instead of False
        return None
    return self.validateAttrib(method, cls)

AttributeSelector.wantMethod = wantMethod
