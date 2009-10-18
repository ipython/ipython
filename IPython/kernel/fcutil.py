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

import os
import tempfile

from twisted.internet import reactor, defer
from twisted.python import log

from foolscap import Tub, UnauthenticatedTub

from IPython.config.loader import Config

from IPython.kernel.configobjfactory import AdaptedConfiguredObjectFactory

from IPython.kernel.error import SecurityError

from IPython.utils.traitlets import Int, Str, Bool, Instance
from IPython.utils.importstring import import_item

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


def check_furl_file_security(furl_file, secure):
    """Remove the old furl_file if changing security modes."""
    if os.path.isfile(furl_file):
        f = open(furl_file, 'r')
        oldfurl = f.read().strip()
        f.close()
        if (oldfurl.startswith('pb://') and not secure) or (oldfurl.startswith('pbu://') and secure):
            os.remove(furl_file)


def is_secure(furl):
    """Is the given FURL secure or not."""
    if is_valid(furl):
        if furl.startswith("pb://"):
            return True
        elif furl.startswith("pbu://"):
            return False
    else:
        raise ValueError("invalid FURL: %s" % furl)


def is_valid(furl):
    """Is the str a valid FURL or not."""
    if isinstance(furl, str):
        if furl.startswith("pb://") or furl.startswith("pbu://"):
            return True
    else:
        return False


def find_furl(furl_or_file):
    """Find, validate and return a FURL in a string or file."""
    if isinstance(furl_or_file, str):
        if is_valid(furl_or_file):
            return furl_or_file
    if os.path.isfile(furl_or_file):
        furl = open(furl_or_file, 'r').read().strip()
        if is_valid(furl):
            return furl
    raise ValueError("not a FURL or a file containing a FURL: %s" % furl_or_file)


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
    instance that has a number of Foolscap references registered in it.
    This class is a subclass of :class:`IPython.core.component.Component`
    so the IPython configuration and component system are used.

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
        file appears, the buffer has been flushed and the file closed.
        """
        temp_furl_file = get_temp_furlfile(furl_file)
        self.tub.registerReference(ref, furlFile=temp_furl_file)
        os.rename(temp_furl_file, furl_file)

