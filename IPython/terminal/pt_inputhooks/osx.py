
# obj-c boilerplate from appnope, used under BSD 2-clause

import ctypes
import ctypes.util

objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('objc'))
CoreFoundation = ctypes.cdll.LoadLibrary(ctypes.util.find_library('CoreFoundation'))
# Cocoa = ctypes.cdll.LoadLibrary(ctypes.util.find_library('Cocoa'))

void_p = ctypes.c_void_p

objc.objc_getClass.restype = void_p
objc.sel_registerName.restype = void_p
objc.objc_msgSend.restype = void_p
objc.objc_msgSend.argtypes = [void_p, void_p]

msg = objc.objc_msgSend

def _utf8(s):
    """ensure utf8 bytes"""
    if not isinstance(s, bytes):
        s = s.encode('utf8')
    return s

def n(name):
    """create a selector name (for methods)"""
    return objc.sel_registerName(_utf8(name))

def C(classname):
    """get an ObjC Class by name"""
    return objc.objc_getClass(_utf8(classname))

# CoreFoundation calls we will use:
CFFileDescriptorCreate = CoreFoundation.CFFileDescriptorCreate
CFFileDescriptorCreate.restype = void_p
CFFileDescriptorCreate.argtypes = [void_p, ctypes.c_int, ctypes.c_bool, void_p]

CFFileDescriptorGetNativeDescriptor = CoreFoundation.CFFileDescriptorGetNativeDescriptor
CFFileDescriptorGetNativeDescriptor.restype = ctypes.c_int
CFFileDescriptorGetNativeDescriptor.argtypes = [void_p]

CFFileDescriptorEnableCallBacks = CoreFoundation.CFFileDescriptorEnableCallBacks
CFFileDescriptorEnableCallBacks.restype = None
CFFileDescriptorEnableCallBacks.argtypes = [void_p, ctypes.c_ulong]

CFFileDescriptorCreateRunLoopSource = CoreFoundation.CFFileDescriptorCreateRunLoopSource
CFFileDescriptorCreateRunLoopSource.restype = void_p
CFFileDescriptorCreateRunLoopSource.argtypes = [void_p, void_p, void_p]

CFRunLoopGetCurrent = CoreFoundation.CFRunLoopGetCurrent
CFRunLoopGetCurrent.restype = void_p

CFRunLoopAddSource = CoreFoundation.CFRunLoopAddSource
CFRunLoopAddSource.restype = None
CFRunLoopAddSource.argtypes = [void_p, void_p, void_p]

CFRelease = CoreFoundation.CFRelease
CFRelease.restype = None
CFRelease.argtypes = [void_p]

CFFileDescriptorInvalidate = CoreFoundation.CFFileDescriptorInvalidate
CFFileDescriptorInvalidate.restype = None
CFFileDescriptorInvalidate.argtypes = [void_p]


# From CFFileDescriptor.h
kCFFileDescriptorReadCallBack = 1
kCFRunLoopCommonModes = void_p.in_dll(CoreFoundation, 'kCFRunLoopCommonModes')

def _NSApp():
    """Return the global NSApplication instance (NSApp)"""
    return msg(C('NSApplication'), n('sharedApplication'))

def _input_callback(fdref, flags, info):
    """Callback to fire when there's input to be read"""
    CFFileDescriptorInvalidate(fdref)
    CFRelease(fdref)
    NSApp = _NSApp()
    msg(NSApp, n('stop:'), NSApp)

_c_callback_func_type = ctypes.CFUNCTYPE(None, void_p, void_p, void_p)
_c_callback = _c_callback_func_type(_input_callback)

def _stop_on_read(fd):
    """Register callback to stop eventloop when there's data on fd"""
    fdref = CFFileDescriptorCreate(None, fd, False, _c_callback, None)
    CFFileDescriptorEnableCallBacks(fdref, kCFFileDescriptorReadCallBack)
    source = CFFileDescriptorCreateRunLoopSource(None, fdref, 0)
    loop = CFRunLoopGetCurrent()
    CFRunLoopAddSource(loop, source, kCFRunLoopCommonModes)
    CFRelease(source)

def inputhook(context):
    """Inputhook for Cocoa (NSApp)"""
    NSApp = _NSApp()
    window_count = msg(
        msg(NSApp, n('windows')),
        n('count')
    )
    if not window_count:
        return
    _stop_on_read(context.fileno())
    msg(NSApp, n('run'))
