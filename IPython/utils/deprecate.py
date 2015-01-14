# encoding: utf-8
#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# from  IPython import version_info
from contextlib import contextmanager
version_info = (3,0,0)

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


# the goal here is to provide a set of deprecatoin utils 
# that help in 
# 1) warning the user/dev
# 2) be explicit in when what will be dropped. 
# 3) help getting rid of the deprecated code once reached the 
#   targetted version. 
#
# To do so: 
# 
# The module/class should provide a global flag that warn or raise as soon as a depercated feature is **used**.
# 
# Each decorator/context manager/... should take a specific version as input to ensure above behavior and raise
# if project behavior go above this point at compile time. (potetially being able to disble this)
# Decorators/with 
#
#
#
# Ok so stages matrix are :
#
#
# no decorator, notn deprecated.
#
# decorator with version V limit/
#       X <  V (deprecation stage)
#       X => V (deprecated  stage)  

# deprecation stage:
#       (lambda_user: nothing)
#       lib_user: -warning
#                 -raise on use if flag
#
# deprecated stage:
#       raise as early as possible.



class DeprecationSingleton(object):
    pass
    
    _sing = None

    @classmethod
    def instance():
        if not _sing:
            _sig = DeprecationSingleton()
        return _sing

import os
nocompat = os.environ.get('NO_COMPAT',False)
more_time_please = os.environ.get('MORE_TIME_PLEASE',False)

features = {'2.7', '3.x'}
def should_cleanup(version):
    if (version_info >= version) and not more_time_please:
        raise DeprecationWarning('Deprecated feature, you can remove some code')


def _comp(value):
    if type(value) is tuple:
        return version_info >= value 
    elif type(value) is str:
        return (value not in features)


@contextmanager
def with_deprecate(version):
    if _comp(version):
        raise DeprecationWarning('Deprecated feature')
    yield


class WithClass( object ):
    def __init__( self, version, nocompat=True):
        self.version = version
        self._noc = nocompat
        should_cleanup(version)


    def __enter__( self ):
        if _comp(self.version) or (nocompat and self._noc):
            raise DeprecationWarning('You shoudl not use that')

    def __exit__( self, type, value, tb ):
        pass


def dec_deprecated(version):

    def _dec(func):
        if _comp(version):
            #raise DeprecationWarning('Deprecated feature')
            def _raise(*args,**kwargs):
                print("I raise an exeption")
                #raise DeprecationWarning('Deprecated feature')
                return func(*args, **kwargs)
            print('should raise on call')
            return _raise
        else :
            print('should return function as is')
            return func
    return _dec


## this is a decorator that shoud do ...
def on_call(version):
    should_cleanup(version)
    def _dec(func):
        if True:
            def _raise(*args,**kwargs):
                if _comp(version) or nocompat:
                    raise DeprecationWarning('This is a deprecated feature, it will eb removed after %s ' % str(version))
                else:
                    return func(*args,**kwargs)
            return _raise
        else :
            return func
    return _dec
