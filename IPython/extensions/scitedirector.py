import win32api
import win32gui
import win32con

import struct
import array

def findWindows():
    ret = []
    sdi = win32api.RegisterWindowMessage("SciTEDirectorInterface")
    w = win32gui.GetWindow(win32gui.GetDesktopWindow(), win32con.GW_CHILD)
    while w:
        res = win32gui.SendMessage(w, sdi, 0, 0)
        if res == sdi:
            ret.append(w)
        w = win32gui.GetWindow(w, win32con.GW_HWNDNEXT)

    return ret

def sendCommand(w, message):
    CopyDataStruct = "IIP"
    char_buffer = array.array('c', message)
    char_buffer_address = char_buffer.buffer_info()[0]
    char_buffer_size = char_buffer.buffer_info()[1]
    cds = struct.pack(CopyDataStruct, 0, char_buffer_size, char_buffer_address)
    win32gui.SendMessage(w, win32con.WM_COPYDATA, 0, cds)
