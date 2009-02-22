"""
Entry point for a simple application giving a graphical frontend to
ipython.
"""

try:
    import wx
except ImportError, e:
    e.message = """%s
________________________________________________________________________________
You need wxPython to run this application.
""" % e.message
    e.args = (e.message, ) + e.args[1:]
    raise e

import wx.stc  as  stc

from wx_frontend import WxController
import __builtin__


class IPythonXController(WxController):
    """ Sub class of WxController that adds some application-specific
        bindings.
    """

    debug = False

    def __init__(self, *args, **kwargs):

        if kwargs['colorset'] == 'black':
            self.prompt_in1 = \
            '\n\x01\x1b[0;30m\x02In [\x01\x1b[1;34m\x02$number\x01\x1b[0;30m\x02]: \x01\x1b[0m\x02'

            self.prompt_out = \
                '\x01\x1b[0;31m\x02Out[\x01\x1b[1;31m\x02$number\x01\x1b[0;31m\x02]: \x01\x1b[0m\x02'
    
        WxController.__init__(self, *args, **kwargs)
        self.ipython0.ask_exit = self.do_exit

        if kwargs['colorset'] == 'black':

            self.carret_color = 'WHITE'
            self.background_color = 'BLACK'
            
            self.SetEdgeMode(stc.STC_EDGE_LINE)
            self.SetEdgeColumn(88)
            
            self.style = {
                    #'stdout'      : '',#fore:#0000FF',
                    #'stderr'      : '',#fore:#007f00',
                    #'trace'       : '',#fore:#FF0000',

                    #'bracegood'   : 'fore:#0000FF,back:#0000FF,bold',
                    #'bracebad'    : 'fore:#FF0000,back:#0000FF,bold',
                    'default'       : "fore:%s,back:%s,size:%d,face:%s,bold" 
                                      % ("#EEEEEE", self.background_color,
                                         self.faces['size'], self.faces['mono']),

                    # properties for the various Python lexer styles
                    'comment'       : 'fore:#BBBBBB,italic',
                    'number'        : 'fore:#FF9692',
                    'string'        : 'fore:#ed9d13,italic',
                    'char'          : 'fore:#FFFFFF,italic',
                    'keyword'       : 'fore:#6AB825,bold',
                    'triple'        : 'fore:#FF7BDD',
                    'tripledouble'  : 'fore:#FF7BDD',
                    'class'         : 'fore:#FF00FF,bold,underline',
                    'def'           : 'fore:#FFFF00,bold',
                    'operator'      : 'bold'
                    }
                                
            #we define the background of old inputs
            self._COMPLETE_BUFFER_BG = '#000000' # RRGGBB: Black
            #we define the background of current input
            self._INPUT_BUFFER_BG = '#444444' # RRGGBB: Light black
            #we define the background when an error is reported
            self._ERROR_BG = '#800000' #'#d22323' #'#AE0021' # RRGGBB: Black
            
            self.set_new_style()

        # Scroll to top
        maxrange = self.GetScrollRange(wx.VERTICAL)
        self.ScrollLines(-maxrange)


    def _on_key_down(self, event, skip=True):
        # Intercept Ctrl-D to quit
        if event.KeyCode == ord('D') and event.ControlDown() and \
                self.input_buffer == '' and \
                self._input_state == 'readline':
            wx.CallAfter(self.ask_exit)
        else:
            WxController._on_key_down(self, event, skip=skip) 


    def ask_exit(self):
        """ Ask the user whether to exit.
        """
        self._input_state = 'subprocess'
        self.write('\n', refresh=False)
        self.capture_output()
        self.ipython0.shell.exit()
        self.release_output()
        if not self.ipython0.exit_now:
            wx.CallAfter(self.new_prompt,
                         self.input_prompt_template.substitute(
                                number=self.last_result['number'] + 1))
        else:
            wx.CallAfter(wx.GetApp().Exit)
        self.write('Exiting ...', refresh=False)
 

    def do_exit(self):
        """ Exits the interpreter, kills the windows.
        """
        WxController.do_exit(self)
        self.release_output()
        wx.CallAfter(wx.Exit)



class IPythonX(wx.Frame):
    """ Main frame of the IPythonX app.
    """

    def __init__(self, parent, id, title, debug=False, colorset='white'):
        wx.Frame.__init__(self, parent, id, title, size=(300,250))
        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self.shell = IPythonXController(self, debug=debug, colorset=colorset)
        self._sizer.Add(self.shell, 1, wx.EXPAND)
        self.SetSizer(self._sizer)
        self.SetAutoLayout(1)
        self.Show(True)
        wx.EVT_CLOSE(self, self.on_close)

        
    def on_close(self, event):
        """ Called on closing the windows. 
            
            Stops the event loop, to close all the child windows.
        """
        wx.CallAfter(wx.Exit)


def main():
    from optparse import OptionParser
    usage = """usage: %prog [options]

Simple graphical frontend to IPython, using WxWidgets."""
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--debug",
                    action="store_true", dest="debug", default=False,
                    help="Enable debug message for the wx frontend.")

    parser.add_option("-s", "--style",
                    dest="colorset", default="white",
                    help="style: white, black")

    options, args = parser.parse_args()

    # Clear the options, to avoid having the ipython0 instance complain
    import sys
    sys.argv = sys.argv[:1]

    app = wx.PySimpleApp()
    frame = IPythonX(None, wx.ID_ANY, 'IPythonX', debug=options.debug, colorset=options.colorset)
    frame.shell.SetFocus()
    frame.shell.app = app
    frame.SetSize((680, 460))

    app.MainLoop()

if __name__ == '__main__':
    main()
