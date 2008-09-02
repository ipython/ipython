#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import wx.aui
import sys
#used for about dialog
from wx.lib.wordwrap import wordwrap

#used for ipython GUI objects
from IPython.gui.wx.ipython_view import IPShellWidget
from IPython.gui.wx.ipython_history import IPythonHistoryPanel

#used to create options.conf file in user directory
from IPython.ipapi import get

__version__ = 0.8
__author__  = "Laurent Dufrechou"
__email__   = "laurent.dufrechou _at_ gmail.com"
__license__ = "BSD"

#-----------------------------------------
# Creating one main frame for our 
# application with movables windows
#-----------------------------------------
class MyFrame(wx.Frame):
    """Creating one main frame for our 
    application with movables windows"""
    def __init__(self, parent=None, id=-1, title="WxIPython", 
                pos=wx.DefaultPosition,
                size=(800, 600), style=wx.DEFAULT_FRAME_STYLE):
        wx.Frame.__init__(self, parent, id, title, pos, size, style)
        self._mgr = wx.aui.AuiManager()
        
        # notify PyAUI which frame to use
        self._mgr.SetManagedWindow(self)
        
        #create differents panels and make them persistant 
        self.history_panel    = IPythonHistoryPanel(self)

        self.history_panel.setOptionTrackerHook(self.optionSave)
        
        self.ipython_panel    = IPShellWidget(self,background_color = "BLACK")
        #self.ipython_panel    = IPShellWidget(self,background_color = "WHITE")

        self.ipython_panel.setHistoryTrackerHook(self.history_panel.write)
        self.ipython_panel.setStatusTrackerHook(self.updateStatus)
        self.ipython_panel.setAskExitHandler(self.OnExitDlg)
        self.ipython_panel.setOptionTrackerHook(self.optionSave)

        self.optionLoad()
        
        self.statusbar = self.createStatus()
        self.createMenu()
        
        ########################################################################
        ### add the panes to the manager
        # main panels
        self._mgr.AddPane(self.ipython_panel , wx.CENTER, "IPython Shell")
        self._mgr.AddPane(self.history_panel , wx.RIGHT,  "IPython history")
                
        # now we specify some panel characteristics
        self._mgr.GetPane(self.ipython_panel).CaptionVisible(True);
        self._mgr.GetPane(self.history_panel).CaptionVisible(True);
        self._mgr.GetPane(self.history_panel).MinSize((200,400));
        
        # tell the manager to "commit" all the changes just made
        self._mgr.Update()

        #global event handling
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_MENU,  self.OnClose,id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU,  self.OnShowIPythonPanel,id=wx.ID_HIGHEST+1)
        self.Bind(wx.EVT_MENU,  self.OnShowHistoryPanel,id=wx.ID_HIGHEST+2)
        self.Bind(wx.EVT_MENU,  self.OnShowAbout, id=wx.ID_HIGHEST+3)
        self.Bind(wx.EVT_MENU,  self.OnShowAllPanel,id=wx.ID_HIGHEST+6)
        
        warn_text = 'Hello from IPython and wxPython.\n'
        warn_text +='Please Note that this work is still EXPERIMENTAL\n'
        warn_text +='It does NOT emulate currently all the IPython functions.\n'
        
        dlg = wx.MessageDialog(self,
                               warn_text,
                               'Warning Box',
                               wx.OK | wx.ICON_INFORMATION
                               )
        dlg.ShowModal()
        dlg.Destroy()

    def optionSave(self, name, value):
        ip = get()
        path = ip.IP.rc.ipythondir
        opt = open(path + '/options.conf','w')

        try:
            options_ipython_panel = self.ipython_panel.getOptions()
            options_history_panel = self.history_panel.getOptions()

            for key in options_ipython_panel.keys():
                opt.write(key + '=' + options_ipython_panel[key]['value']+'\n')
            for key in options_history_panel.keys():
                opt.write(key + '=' + options_history_panel[key]['value']+'\n')
        finally:    
            opt.close()
        
    def optionLoad(self):
        try:
            ip = get()
            path = ip.IP.rc.ipythondir
            opt = open(path + '/options.conf','r')
            lines = opt.readlines()
            opt.close()
                      
            options_ipython_panel = self.ipython_panel.getOptions()
            options_history_panel = self.history_panel.getOptions()
            
            for line in lines:
                key = line.split('=')[0]
                value = line.split('=')[1].replace('\n','').replace('\r','')
                if key in options_ipython_panel.keys():
                    options_ipython_panel[key]['value'] = value
                elif key in options_history_panel.keys():
                    options_history_panel[key]['value'] = value
                else:
                    print >>sys.__stdout__,"Warning: key ",key,"not found in widget options. Check Options.conf"
            self.ipython_panel.reloadOptions(options_ipython_panel)
            self.history_panel.reloadOptions(options_history_panel)
        
        except IOError:
            print >>sys.__stdout__,"Could not open Options.conf, defaulting to default values."
            
        
    def createMenu(self):
        """local method used to create one menu bar"""
        
        mb = wx.MenuBar()

        file_menu = wx.Menu()
        file_menu.Append(wx.ID_EXIT, "Exit")
        
        view_menu = wx.Menu()
        view_menu.Append(wx.ID_HIGHEST+1, "Show IPython Panel")
        view_menu.Append(wx.ID_HIGHEST+2, "Show History Panel")
        view_menu.AppendSeparator()
        view_menu.Append(wx.ID_HIGHEST+6, "Show All")
        
        about_menu = wx.Menu()
        about_menu.Append(wx.ID_HIGHEST+3, "About")

        #view_menu.AppendSeparator()
        #options_menu = wx.Menu()
        #options_menu.AppendCheckItem(wx.ID_HIGHEST+7, "Allow Floating")
        #options_menu.AppendCheckItem(wx.ID_HIGHEST+8, "Transparent Hint")
        #options_menu.AppendCheckItem(wx.ID_HIGHEST+9, "Transparent Hint Fade-in")
        
        
        mb.Append(file_menu, "File")
        mb.Append(view_menu, "View")
        mb.Append(about_menu, "About")
        #mb.Append(options_menu, "Options")
        
        self.SetMenuBar(mb)

    def createStatus(self):
        statusbar = self.CreateStatusBar(2, wx.ST_SIZEGRIP)
        statusbar.SetStatusWidths([-2, -3])
        statusbar.SetStatusText("Ready", 0)
        statusbar.SetStatusText("WxIPython "+str(__version__), 1)
        return statusbar

    def updateStatus(self,text):
        states = {'IDLE':'Idle',
                  'DO_EXECUTE_LINE':'Send command',
                  'WAIT_END_OF_EXECUTION':'Running command',
                  'WAITING_USER_INPUT':'Waiting user input',
                  'SHOW_DOC':'Showing doc',
                  'SHOW_PROMPT':'Showing prompt'}
        self.statusbar.SetStatusText(states[text], 0)
        
    def OnClose(self, event):
        """#event used to close program  """
        # deinitialize the frame manager
        self._mgr.UnInit()
        self.Destroy()        
        event.Skip()
    
    def OnExitDlg(self, event):
        dlg = wx.MessageDialog(self, 'Are you sure you want to quit WxIPython',
                                'WxIPython exit',
                                wx.ICON_QUESTION |
                                wx.YES_NO | wx.NO_DEFAULT
                                )
        if dlg.ShowModal() == wx.ID_YES:
            dlg.Destroy()
            self._mgr.UnInit()
            self.Destroy()
        dlg.Destroy()
      
    #event to display IPython pannel      
    def OnShowIPythonPanel(self,event):
        """ #event to display Boxpannel """
        self._mgr.GetPane(self.ipython_panel).Show(True)
        self._mgr.Update()  
    #event to display History pannel      
    def OnShowHistoryPanel(self,event):
        self._mgr.GetPane(self.history_panel).Show(True)
        self._mgr.Update()  
         
    def OnShowAllPanel(self,event):
        """#event to display all Pannels"""
        self._mgr.GetPane(self.ipython_panel).Show(True)
        self._mgr.GetPane(self.history_panel).Show(True)
        self._mgr.Update()

    def OnShowAbout(self, event):
        # First we create and fill the info object
        info = wx.AboutDialogInfo()
        info.Name = "WxIPython"
        info.Version = str(__version__)
        info.Copyright = "(C) 2007 Laurent Dufrechou"
        info.Description = wordwrap(
            "A Gui that embbed a multithreaded IPython Shell",
            350, wx.ClientDC(self))
        info.WebSite = ("http://ipython.scipy.org/", "IPython home page")
        info.Developers = [ "Laurent Dufrechou" ]
        licenseText="BSD License.\nAll rights reserved. This program and the accompanying materials are made available under the terms of the BSD which accompanies this distribution, and is available at http://www.opensource.org/licenses/bsd-license.php"
        info.License = wordwrap(licenseText, 500, wx.ClientDC(self))

        # Then we call wx.AboutBox giving it that info object
        wx.AboutBox(info) 
        
#-----------------------------------------
#Creating our application
#----------------------------------------- 
class MyApp(wx.PySimpleApp):
    """Creating our application"""
    def __init__(self):
        wx.PySimpleApp.__init__(self)
        
        self.frame = MyFrame()
        self.frame.Show()
        
#-----------------------------------------
#Main loop
#----------------------------------------- 
def main():
    app = MyApp()
    app.SetTopWindow(app.frame)
    app.MainLoop()

#if launched as main program run this
if __name__ == '__main__':
    main()
