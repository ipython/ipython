import IPython.ipapi
import win32clipboard

ip = IPython.ipapi.get()

def clip_f(self,parameter_s = ''):
       """Save a set of lines to the clipboard.

       Usage:\\
         %clip n1-n2 n3-n4 ... n5 .. n6 ...

       This function uses the same syntax as %macro for line extraction, but
       instead of creating a macro it saves the resulting string to the
       clipboard."""

       args = parameter_s.split()
       if len(args) == 0:
           return None # xxx todo return clipboard text
       
       ranges = args[0:]
       cmds = ''.join(self.extract_input_slices(ranges))
       win32clipboard.OpenClipboard()
       win32clipboard.EmptyClipboard()
       win32clipboard.SetClipboardText(cmds)
       win32clipboard.CloseClipboard()
       print 'The following commands were written to the clipboard'
       print cmds

ip.expose_magic("clip",clip_f)