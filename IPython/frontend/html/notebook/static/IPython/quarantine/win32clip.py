from IPython.core import ipapi

ip = ipapi.get()

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
    api = self.getapi()

    if parameter_s.lstrip().startswith('='):
        rest = parameter_s[parameter_s.index('=')+1:].strip()
        val = str(api.ev(rest))
    else:
        ranges = args[0:]
        val = ''.join( self.extract_input_slices( ranges ) )

    cl.EmptyClipboard()
    cl.SetClipboardText( val )
    cl.CloseClipboard()
    print 'The following text was written to the clipboard'
    print val

ip.define_magic( "clip", clip_f )
