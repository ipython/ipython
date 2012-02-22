"""The IPython HTML Notebook"""

# check for tornado 2.1.0
msg = "The IPython Notebook requires tornado >= 2.1.0"
try:
    import tornado
except ImportError:
    raise ImportError(msg)
try:
    version_info = tornado.version_info
except AttributeError:
    raise ImportError(msg + ", but you have < 1.1.0")
if version_info < (2,1,0):
    raise ImportError(msg + ", but you have %s" % tornado.version)
del msg
