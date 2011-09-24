"""The IPython HTML Notebook"""

# check for tornado 2.1.0
msg = "The IPython Notebook requires tornado >= 2.1.0"
try:
    import tornado
except ImportError:
    raise ImportError(msg)
else:
    if tornado.version_info < (2,1,0):
        raise ImportError(msg+", but you have %s"%tornado.version)
del msg
