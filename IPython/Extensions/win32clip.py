import IPython.ipapi

ip = IPython.ipapi.get()

def clip_f( self, parameter_s = '' ):
    """Save a set of lines to the clipboard.

    Usage:\\
      %clip n1-n2 n3-n4 ... n5 .. n6 ...

    This function uses the same syntax as %macro for line extraction, but
    instead of creating a macro it saves the resulting string to the
    clipboard.
    
    When used without arguments, this returns the text contents of the clipboard. 
    E.g.
    
    mytext = %clip
    
    """

    import win32clipboard as cl
    import win32con
    args = parameter_s.split()
    cl.OpenClipboard()
    if len( args ) == 0:
        data = cl.GetClipboardData( win32con.CF_TEXT )
        cl.CloseClipboard()
        return data

    ranges = args[0:]
    cmds = ''.join( self.extract_input_slices( ranges ) )

    cl.EmptyClipboard()
    cl.SetClipboardText( cmds )
    cl.CloseClipboard()
    print 'The following commands were written to the clipboard'
    print cmds
    
ip.expose_magic( "clip", clip_f )
