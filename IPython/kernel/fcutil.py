#!/usr/bin/env python
# encoding: utf-8
"""
Foolscap related utilities.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import with_statement

import os
import tempfile

from twisted.internet import reactor, defer
from twisted.python import log

import foolscap
try:
    from foolscap.api import Tub, UnauthenticatedTub
except ImportError:
    from foolscap import Tub, UnauthenticatedTub

from IPython.config.loader import Config
from IPython.kernel.configobjfactory import AdaptedConfiguredObjectFactory
from IPython.kernel.error import SecurityError

from IPython.utils.importstring import import_item
from IPython.utils.path import expand_path
from IPython.utils.traitlets import Int, Str, Bool, Instance

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


# We do this so if a user doesn't have OpenSSL installed, it will try to use
# an UnauthenticatedTub.  But, they will still run into problems if they
# try to use encrypted furls.
try:
    import OpenSSL
except:
    Tub = UnauthenticatedTub
    have_crypto = False
else:
    have_crypto = True


class FURLError(Exception):
    pass


def check_furl_file_security(furl_file, secure):
    """Remove the old furl_file if changing security modes."""
    furl_file = expand_path(furl_file)
    if os.path.isfile(furl_file):
        with open(furl_file, 'r') as f:
            oldfurl = f.read().strip()
        if (oldfurl.startswith('pb://') and not secure) or (oldfurl.startswith('pbu://') and secure):
            os.remove(furl_file)


def is_secure(furl):
    """Is the given FURL secure or not."""
    if is_valid_furl(furl):
        if furl.startswith("pb://"):
            return True
        elif furl.startswith("pbu://"):
            return False
    else:
        raise FURLError("invalid FURL: %s" % furl)


def is_valid_furl(furl):
    """Is the str a valid FURL or not."""
    if isinstance(furl, str):
        if furl.startswith("pb://") or furl.startswith("pbu://"):
            return True
        else:
            return False
    else:
        return False


def is_valid_furl_file(furl_or_file):
    """See if furl_or_file exists and contains a valid FURL.

    This doesn't try to read the contents because often we have to validate
    FURL files that are created, but don't yet have a FURL written to them.
    """
    if isinstance(furl_or_file, (str, unicode)):
        path, furl_filename = os.path.split(furl_or_file)
        if os.path.isdir(path) and furl_filename.endswith('.furl'):
            return True
    return False


def find_furl(furl_or_file):
    """Find, validate and return a FURL in a string or file.

    This calls :func:`IPython.utils.path.expand_path` on the argument to
    properly handle ``~`` and ``$`` variables in the path.
    """
    if is_valid_furl(furl_or_file):
        return furl_or_file
    furl_or_file = expand_path(furl_or_file)
    if is_valid_furl_file(furl_or_file):
        with open(furl_or_file, 'r') as f:
            furl = f.read().strip()
        if is_valid_furl(furl):
            return furl
    raise FURLError("Not a valid FURL or FURL file: %r" % furl_or_file)


def is_valid_furl_or_file(furl_or_file):
    """Validate a FURL or a FURL file.

    If ``furl_or_file`` looks like a file, we simply make sure its directory
    exists and that it has a ``.furl`` file extension.  We don't try to see
    if the FURL file exists or to read its contents. This is useful for
    cases where auto re-connection is being used.
    """
    if is_valid_furl(furl_or_file) or is_valid_furl_file(furl_or_file):
        return True
    else:
        return False


def validate_furl_or_file(furl_or_file):
    """Like :func:`is_valid_furl_or_file`, but raises an error."""
    if not is_valid_furl_or_file(furl_or_file):
        raise FURLError('Not a valid FURL or FURL file: %r' % furl_or_file)


def get_temp_furlfile(filename):
    """Return a temporary FURL file."""
    return tempfile.mktemp(dir=os.path.dirname(filename),
                           prefix=os.path.basename(filename))


def make_tub(ip, port, secure, cert_file):
    """Create a listening tub given an ip, port, and cert_file location.
    
    Parameters
    ----------
    ip : str
        The ip address or hostname that the tub should listen on.  
        Empty means all interfaces.
    port : int
        The port that the tub should listen on.  A value of 0 means
        pick a random port
    secure: bool
        Will the connection be secure (in the Foolscap sense).
    cert_file: str
        A filename of a file to be used for theSSL certificate.

    Returns
    -------
    A tub, listener tuple.
    """
    if secure:
        if have_crypto:
            tub = Tub(certFile=cert_file)
        else:
            raise SecurityError("OpenSSL/pyOpenSSL is not available, so we "
                                "can't run in secure mode.  Try running without "
                                "security using 'ipcontroller -xy'.")
    else:
        tub = UnauthenticatedTub()
    
    # Set the strport based on the ip and port and start listening
    if ip == '':
        strport = "tcp:%i" % port
    else:
        strport = "tcp:%i:interface=%s" % (port, ip)
    log.msg("Starting listener with [secure=%r] on: %s" % (secure, strport))
    listener = tub.listenOn(strport)
    
    return tub, listener


class FCServiceFactory(AdaptedConfiguredObjectFactory):
    """This class creates a tub with various services running in it.

    The basic idea is that :meth:`create` returns a running :class:`Tub`
    instance that has a number of Foolscap references registered in it. This
    class is a subclass of :class:`IPython.config.configurable.Configurable`
    so the IPython configuration system is used.

    Attributes
    ----------
    interfaces : Config
        A Config instance whose values are sub-Config objects having two
        keys: furl_file and interface_chain.

    The other attributes are the standard ones for Foolscap.
    """

    ip = Str('', config=True)
    port = Int(0, config=True)
    secure = Bool(True, config=True)
    cert_file = Str('', config=True)
    location = Str('', config=True)
    reuse_furls = Bool(False, config=True)
    interfaces = Instance(klass=Config, kw={}, allow_none=False, config=True)

    def __init__(self, config, adaptee):
        super(FCServiceFactory, self).__init__(config, adaptee)
        self._check_reuse_furls()

    def _ip_changed(self, name, old, new):
        if new == 'localhost' or new == '127.0.0.1':
            self.location = '127.0.0.1'

    def _check_reuse_furls(self):
        furl_files = [i.furl_file for i in self.interfaces.values()]
        for ff in furl_files:
            fullfile = self._get_security_file(ff)
            if self.reuse_furls:
                if self.port==0:
                    raise FURLError("You are trying to reuse the FURL file "
                        "for this connection, but the port for this connection "
                        "is set to 0 (autoselect). To reuse the FURL file "
                        "you need to specify specific port to listen on."
                    )
                else:
                    log.msg("Reusing FURL file: %s" % fullfile)
            else:
                if os.path.isfile(fullfile):
                    log.msg("Removing old FURL file: %s" % fullfile)
                    os.remove(fullfile)

    def _get_security_file(self, filename):
        return os.path.join(self.config.Global.security_dir, filename)

    def create(self):
        """Create and return the Foolscap tub with everything running."""

        self.tub, self.listener = make_tub(
            self.ip, self.port, self.secure, 
            self._get_security_file(self.cert_file)
        )
        # log.msg("Interfaces to register [%r]: %r" % \
        #     (self.__class__, self.interfaces))
        if not self.secure:
            log.msg("WARNING: running with no security: %s" % \
                self.__class__.__name__)
        reactor.callWhenRunning(self.set_location_and_register)
        return self.tub

    def set_location_and_register(self):
        """Set the location for the tub and return a deferred."""

        if self.location == '':
            d = self.tub.setLocationAutomatically()
        else:
            d = defer.maybeDeferred(self.tub.setLocation,
                "%s:%i" % (self.location, self.listener.getPortnum()))
        self.adapt_to_interfaces(d)

    def adapt_to_interfaces(self, d):
        """Run through the interfaces, adapt and register."""

        for ifname, ifconfig in self.interfaces.iteritems():
            ff = self._get_security_file(ifconfig.furl_file)
            log.msg("Adapting [%s] to interface: %s" % \
                (self.adaptee.__class__.__name__, ifname))
            log.msg("Saving FURL for interface [%s] to file: %s" % (ifname, ff))
            check_furl_file_security(ff, self.secure)
            adaptee = self.adaptee
            for i in ifconfig.interface_chain:
                adaptee = import_item(i)(adaptee)
            d.addCallback(self.register, adaptee, furl_file=ff)

    def register(self, empty, ref, furl_file):
        """Register the reference with the FURL file.

        The FURL file is created and then moved to make sure that when the
        file appears, the buffer has been flushed and the file closed. This
        is not done if we are re-using FURLS however.
        """
        if self.reuse_furls:
            self.tub.registerReference(ref, furlFile=furl_file)
        else:
            temp_furl_file = get_temp_furlfile(furl_file)
            self.tub.registerReference(ref, furlFile=temp_furl_file)
            os.rename(temp_furl_file, furl_file)

