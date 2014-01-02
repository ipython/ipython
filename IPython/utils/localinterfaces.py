"""Simple utility for building a list of local IPs using the socket module.
This module defines two constants:

LOCALHOST : The loopback interface, or the first interface that points to this
            machine.  It will *almost* always be '127.0.0.1'

LOCAL_IPS : A list of IP addresses, loopback first, that point to this machine.
            This will include LOCALHOST, PUBLIC_IPS, and aliases for all hosts,
            such as '0.0.0.0'.

PUBLIC_IPS : A list of public IP addresses that point to this machine.
             Use these to tell remote clients where to find you.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import re
import socket

from .data import uniq_stable
from .process import get_output_error_code
from .warn import warn

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

LOCAL_IPS = []
PUBLIC_IPS = []

LOCALHOST = ''

def _only_once(f):
    """decorator to only run a function once"""
    f.called = False
    def wrapped(**kwargs):
        if f.called:
            return
        ret = f(**kwargs)
        f.called = True
        return ret
    return wrapped

def _requires_ips(f):
    """decorator to ensure load_ips has been run before f"""
    def ips_loaded(*args, **kwargs):
        _load_ips()
        return f(*args, **kwargs)
    return ips_loaded

# subprocess-parsing ip finders
class NoIPAddresses(Exception):
    pass

def _populate_from_list(addrs):
    """populate local and public IPs from flat list of all IPs"""
    if not addrs:
        raise NoIPAddresses
    
    global LOCALHOST
    public_ips = []
    local_ips = []
    
    for ip in addrs:
        local_ips.append(ip)
        if not ip.startswith('127.'):
            public_ips.append(ip)
        elif not LOCALHOST:
            LOCALHOST = ip
    
    if not LOCALHOST:
        LOCALHOST = '127.0.0.1'
        local_ips.insert(0, LOCALHOST)
        
    local_ips.extend(['0.0.0.0', ''])
    
    LOCAL_IPS[:] = uniq_stable(local_ips)
    PUBLIC_IPS[:] = uniq_stable(public_ips)

def _load_ips_ifconfig():
    """load ip addresses from `ifconfig` output (posix)"""
    
    out, err, rc = get_output_error_code('ifconfig')
    if rc:
        # no ifconfig, it's usually in /sbin and /sbin is not on everyone's PATH
        out, err, rc = get_output_error_code('/sbin/ifconfig')
    if rc:
        raise IOError("no ifconfig: %s" % err)
    
    lines = out.splitlines()
    addrs = []
    for line in lines:
        blocks = line.lower().split()
        if (len(blocks) >= 2) and (blocks[0] == 'inet'):
            if  blocks[1].startswith("addr:"):
                addrs.append(blocks[1].split(":")[1])
            else:
                addrs.append(blocks[1])
    _populate_from_list(addrs)


def _load_ips_ip():
    """load ip addresses from `ip addr` output (Linux)"""
    out, err, rc = get_output_error_code('ip addr')
    if rc:
        raise IOError("no ip: %s" % err)
    
    lines = out.splitlines()
    addrs = []
    for line in lines:
        blocks = line.lower().split()
        if (len(blocks) >= 2) and (blocks[0] == 'inet'):
            addrs.append(blocks[1].split('/')[0])
    _populate_from_list(addrs)

_ipconfig_ipv4_pat = re.compile(r'ipv4.*(\d+\.\d+\.\d+\.\d+)$', re.IGNORECASE)

def _load_ips_ipconfig():
    """load ip addresses from `ipconfig` output (Windows)"""
    out, err, rc = get_output_error_code('ipconfig')
    if rc:
        raise IOError("no ipconfig: %s" % err)
    
    lines = out.splitlines()
    addrs = []
    for line in lines:
        m = _ipconfig_ipv4_pat.match(line.strip())
        if m:
            addrs.append(m.group(1))
    _populate_from_list(addrs)


def _load_ips_netifaces():
    """load ip addresses with netifaces"""
    import netifaces
    global LOCALHOST
    local_ips = []
    public_ips = []
    
    # list of iface names, 'lo0', 'eth0', etc.
    for iface in netifaces.interfaces():
        # list of ipv4 addrinfo dicts
        ipv4s = netifaces.ifaddresses(iface).get(netifaces.AF_INET, [])
        for entry in ipv4s:
            addr = entry.get('addr')
            if not addr:
                continue
            if not (iface.startswith('lo') or addr.startswith('127.')):
                public_ips.append(addr)
            elif not LOCALHOST:
                LOCALHOST = addr
            local_ips.append(addr)
    if not LOCALHOST:
        # we never found a loopback interface (can this ever happen?), assume common default
        LOCALHOST = '127.0.0.1'
        local_ips.insert(0, LOCALHOST)
    local_ips.extend(['0.0.0.0', ''])
    LOCAL_IPS[:] = uniq_stable(local_ips)
    PUBLIC_IPS[:] = uniq_stable(public_ips)


def _load_ips_gethostbyname():
    """load ip addresses with socket.gethostbyname_ex
    
    This can be slow.
    """
    global LOCALHOST
    try:
        LOCAL_IPS[:] = socket.gethostbyname_ex('localhost')[2]
    except socket.error:
        # assume common default
        LOCAL_IPS[:] = ['127.0.0.1']
    
    try:
        hostname = socket.gethostname()
        PUBLIC_IPS[:] = socket.gethostbyname_ex(hostname)[2]
        # try hostname.local, in case hostname has been short-circuited to loopback
        if not hostname.endswith('.local') and all(ip.startswith('127') for ip in PUBLIC_IPS):
            PUBLIC_IPS[:] = socket.gethostbyname_ex(socket.gethostname() + '.local')[2]
    except socket.error:
        pass
    finally:
        PUBLIC_IPS[:] = uniq_stable(PUBLIC_IPS)
        LOCAL_IPS.extend(PUBLIC_IPS)
    
    # include all-interface aliases: 0.0.0.0 and ''
    LOCAL_IPS.extend(['0.0.0.0', ''])

    LOCAL_IPS[:] = uniq_stable(LOCAL_IPS)

    LOCALHOST = LOCAL_IPS[0]

def _load_ips_dumb():
    """Fallback in case of unexpected failure"""
    global LOCALHOST
    LOCALHOST = '127.0.0.1'
    LOCAL_IPS[:] = [LOCALHOST, '0.0.0.0', '']
    PUBLIC_IPS[:] = []

@_only_once
def _load_ips(suppress_exceptions=True):
    """load the IPs that point to this machine
    
    This function will only ever be called once.
    
    It will use netifaces to do it quickly if available.
    Then it will fallback on parsing the output of ifconfig / ip addr / ipconfig, as appropriate.
    Finally, it will fallback on socket.gethostbyname_ex, which can be slow.
    """
    
    try:
        # first priority, use netifaces
        try:
            return _load_ips_netifaces()
        except ImportError:
            pass
        
        # second priority, parse subprocess output (how reliable is this?)
        
        if os.name == 'nt':
            try:
                return _load_ips_ipconfig()
            except (IOError, NoIPAddresses):
                pass
        else:
            try:
                return _load_ips_ifconfig()
            except (IOError, NoIPAddresses):
                pass
            try:
                return _load_ips_ip()
            except (IOError, NoIPAddresses):
                pass
        
        # lowest priority, use gethostbyname
        
        return _load_ips_gethostbyname()
    except Exception as e:
        if not suppress_exceptions:
            raise
        # unexpected error shouldn't crash, load dumb default values instead.
        warn("Unexpected error discovering local network interfaces: %s" % e)
    _load_ips_dumb()


@_requires_ips
def local_ips():
    """return the IP addresses that point to this machine"""
    return LOCAL_IPS

@_requires_ips
def public_ips():
    """return the IP addresses for this machine that are visible to other machines"""
    return PUBLIC_IPS

@_requires_ips
def localhost():
    """return ip for localhost (almost always 127.0.0.1)"""
    return LOCALHOST

@_requires_ips
def is_local_ip(ip):
    """does `ip` point to this machine?"""
    return ip in LOCAL_IPS

@_requires_ips
def is_public_ip(ip):
    """is `ip` a publicly visible address?"""
    return ip in PUBLIC_IPS
