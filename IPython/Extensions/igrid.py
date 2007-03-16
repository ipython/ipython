# -*- coding: iso-8859-1 -*-

import ipipe, os, webbrowser, urllib
import wx
import wx.grid, wx.html

try:
    sorted
except NameError:
    from ipipe import sorted


__all__ = ["igrid"]


class IGridRenderer(wx.grid.PyGridCellRenderer):
    """
    This is a custom renderer for our IGridGrid
    """
    def __init__(self, table):
        self.maxchars = 200
        self.table = table
        self.colormap = (
            (  0,   0,   0),
            (174,   0,   0),
            (  0, 174,   0),
            (174, 174,   0),
            (  0,   0, 174),
            (174,   0, 174),
            (  0, 174, 174),
            ( 64,  64,  64)
        )

        wx.grid.PyGridCellRenderer.__init__(self)

    def _getvalue(self, row, col):
        try:
            value = self.table._displayattrs[col].value(self.table.items[row])
            (align, width, text) = ipipe.xformat(value, "cell", self.maxchars)
        except Exception, exc:
            (align, width, text) = ipipe.xformat(exc, "cell", self.maxchars)
        return (align, text)

    def GetBestSize(self, grid, attr, dc, row, col):
        text = grid.GetCellValue(row, col)
        (align, text) = self._getvalue(row, col)
        dc.SetFont(attr.GetFont())
        (w, h) = dc.GetTextExtent(str(text))
        return wx.Size(min(w+2, 600), h+2) # add border

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        """
        Takes care of drawing everything in the cell; aligns the text
        """
        text = grid.GetCellValue(row, col)
        (align, text) = self._getvalue(row, col)
        if isSelected:
            bg = grid.GetSelectionBackground()
        else:
            bg = ["white", (240, 240, 240)][row%2]
        dc.SetTextBackground(bg)
        dc.SetBrush(wx.Brush(bg, wx.SOLID))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetFont(attr.GetFont())
        dc.DrawRectangleRect(rect)
        dc.SetClippingRect(rect)
        # Format the text
        if align == -1: # left alignment
            (width, height) = dc.GetTextExtent(str(text))
            x = rect[0]+1
            y = rect[1]+0.5*(rect[3]-height)

            for (style, part) in text:
                if isSelected:
                    fg = grid.GetSelectionForeground()
                else:
                    fg = self.colormap[style.fg]
                dc.SetTextForeground(fg)
                (w, h) = dc.GetTextExtent(part)
                dc.DrawText(part, x, y)
                x += w
        elif align == 0: # center alignment
            (width, height) = dc.GetTextExtent(str(text))
            x = rect[0]+0.5*(rect[2]-width)
            y = rect[1]+0.5*(rect[3]-height)
            for (style, part) in text:
                if isSelected:
                    fg = grid.GetSelectionForeground()
                else:
                    fg = self.colormap[style.fg]
                dc.SetTextForeground(fg)
                (w, h) = dc.GetTextExtent(part)
                dc.DrawText(part, x, y)
                x += w
        else:  # right alignment
            (width, height) = dc.GetTextExtent(str(text))
            x = rect[0]+rect[2]-1
            y = rect[1]+0.5*(rect[3]-height)
            for (style, part) in reversed(text):
                (w, h) = dc.GetTextExtent(part)
                x -= w
                if isSelected:
                    fg = grid.GetSelectionForeground()
                else:
                    fg = self.colormap[style.fg]
                dc.SetTextForeground(fg)
                dc.DrawText(part, x, y)
        dc.DestroyClippingRegion()

    def Clone(self):
        return IGridRenderer(self.table)


class IGridTable(wx.grid.PyGridTableBase):
    # The data table for the ``IGridGrid``. Some dirty tricks were used here:
    # ``GetValue()`` does not get any values (or at least it does not return
    # anything, accessing the values is done by the renderer)
    # but rather tries to fetch the objects which were requested into the table.
    # General behaviour is: Fetch the first X objects. If the user scrolls down
    # to the last object another bunch of X objects is fetched (if possible)
    def __init__(self, input, fontsize, *attrs):
        wx.grid.PyGridTableBase.__init__(self)
        self.input = input
        self.iterator = ipipe.xiter(input)
        self.items = []
        self.attrs = [ipipe.upgradexattr(attr) for attr in attrs]
        self._displayattrs = self.attrs[:]
        self._displayattrset = set(self.attrs)
        self._sizing = False
        self.fontsize = fontsize
        self._fetch(1)

    def GetAttr(self, *args):
        attr = wx.grid.GridCellAttr()
        attr.SetFont(wx.Font(self.fontsize, wx.TELETYPE, wx.NORMAL, wx.NORMAL))
        return attr

    def GetNumberRows(self):
        return len(self.items)

    def GetNumberCols(self):
        return len(self._displayattrs)

    def GetColLabelValue(self, col):
        if col < len(self._displayattrs):
            return self._displayattrs[col].name()
        else:
            return ""

    def GetRowLabelValue(self, row):
        return str(row)

    def IsEmptyCell(self, row, col):
        return False

    def _append(self, item):
        self.items.append(item)
        # Nothing to do if the set of attributes has been fixed by the user
        if not self.attrs:
            for attr in ipipe.xattrs(item):
                attr = ipipe.upgradexattr(attr)
                if attr not in self._displayattrset:
                    self._displayattrs.append(attr)
                    self._displayattrset.add(attr)

    def _fetch(self, count):
        # Try to fill ``self.items`` with at least ``count`` objects.
        have = len(self.items)
        while self.iterator is not None and have < count:
            try:
                item = self.iterator.next()
            except StopIteration:
                self.iterator = None
                break
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception, exc:
                have += 1
                self._append(item)
                self.iterator = None
                break
            else:
                have += 1
                self._append(item)

    def GetValue(self, row, col):
        # some kind of dummy-function: does not return anything but "";
        # (The value isn't use anyway)
        # its main task is to trigger the fetch of new objects
        had_cols = self._displayattrs[:]
        had_rows = len(self.items)
        if row == had_rows - 1 and self.iterator is not None and not self._sizing:
            self._fetch(row + 20)
        have_rows = len(self.items)
        have_cols = len(self._displayattrs)
        if have_rows > had_rows:
            msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED, have_rows - had_rows)
            self.GetView().ProcessTableMessage(msg)
            self._sizing = True
            self.GetView().AutoSizeColumns(False)
            self._sizing = False
        if row >= have_rows:
            return ""
        if self._displayattrs != had_cols:
            msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED, have_cols - len(had_cols))
            self.GetView().ProcessTableMessage(msg)
        return ""

    def SetValue(self, row, col, value):
        pass


class IGridGrid(wx.grid.Grid):
    # The actual grid
    # all methods for selecting/sorting/picking/... data are implemented here
    def __init__(self, panel, input, *attrs):
        wx.grid.Grid.__init__(self, panel)
        fontsize = 9
        self.input = input
        self.table = IGridTable(self.input, fontsize, *attrs)
        self.SetTable(self.table, True)
        self.SetSelectionMode(wx.grid.Grid.wxGridSelectRows)
        self.SetDefaultRenderer(IGridRenderer(self.table))
        self.EnableEditing(False)
        self.Bind(wx.EVT_KEY_DOWN, self.key_pressed)
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.cell_doubleclicked)
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.cell_leftclicked)
        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_DCLICK, self.label_doubleclicked)
        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.on_label_leftclick)
        self.Bind(wx.grid.EVT_GRID_RANGE_SELECT, self._on_selected_range)
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self._on_selected_cell)
        self.current_selection = set()
        self.maxchars = 200

    def on_label_leftclick(self, event):
        event.Skip()

    def error_output(self, text):
        wx.Bell()
        frame = self.GetParent().GetParent().GetParent()
        frame.SetStatusText(text)

    def _on_selected_range(self, event):
        # Internal update to the selection tracking lists
        if event.Selecting():
            # adding to the list...
            self.current_selection.update(xrange(event.GetTopRow(), event.GetBottomRow()+1))
        else:
            # removal from list
            for index in xrange( event.GetTopRow(), event.GetBottomRow()+1):
                self.current_selection.discard(index)
        event.Skip()

    def _on_selected_cell(self, event):
        # Internal update to the selection tracking list
        self.current_selection = set([event.GetRow()])
        event.Skip()

    def sort(self, key, reverse=False):
        """
        Sort the current list of items using the key function ``key``. If
        ``reverse`` is true the sort order is reversed.
        """
        row = self.GetGridCursorRow()
        col = self.GetGridCursorCol()
        curitem = self.table.items[row] # Remember where the cursor is now
        # Sort items
        def realkey(item):
            try:
                return key(item)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                return None
        try:
            self.table.items = ipipe.deque(sorted(self.table.items, key=realkey, reverse=reverse))
        except TypeError, exc:
            self.error_output("Exception encountered: %s" % exc)
            return
        # Find out where the object under the cursor went
        for (i, item) in enumerate(self.table.items):
            if item is curitem:
                self.SetGridCursor(i,col)
                self.MakeCellVisible(i,col)
                self.Refresh()

    def sortattrasc(self):
        """
        Sort in ascending order; sorting criteria is the current attribute
        """
        col = self.GetGridCursorCol()
        attr = self.table._displayattrs[col]
        frame = self.GetParent().GetParent().GetParent()
        if attr is ipipe.noitem:
            self.error_output("no column under cursor")
            return
        frame.SetStatusText("sort by %s (ascending)" % attr.name())
        def key(item):
            try:
                return attr.value(item)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                return None
        self.sort(key)

    def sortattrdesc(self):
        """
        Sort in descending order; sorting criteria is the current attribute
        """
        col = self.GetGridCursorCol()
        attr = self.table._displayattrs[col]
        frame = self.GetParent().GetParent().GetParent()
        if attr is ipipe.noitem:
            self.error_output("no column under cursor")
            return
        frame.SetStatusText("sort by %s (descending)" % attr.name())
        def key(item):
            try:
                return attr.value(item)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                return None
        self.sort(key, reverse=True)

    def label_doubleclicked(self, event):
        row = event.GetRow()
        col = event.GetCol()
        if col == -1:
            self.enter(row)

    def _getvalue(self, row, col):
        """
        Gets the text which is displayed at ``(row, col)``
        """
        try:
            value = self.table._displayattrs[col].value(self.table.items[row])
            (align, width, text) = ipipe.xformat(value, "cell", self.maxchars)
        except IndexError:
            raise IndexError
        except Exception, exc:
            (align, width, text) = ipipe.xformat(exc, "cell", self.maxchars)
        return text

    def search(self, searchtext, startrow=0, startcol=0, search_forward=True):
        """
        search for ``searchtext``, starting in ``(startrow, startcol)``;
        if ``search_forward`` is true the direction is "forward"
        """
        row = startrow
        searchtext = searchtext.lower()
        if search_forward:
            while True:
                for col in xrange(startcol, self.table.GetNumberCols()):
                    try:
                        foo = self.table.GetValue(row, col)
                        text = self._getvalue(row, col)
                        if searchtext in text.string().lower():
                            self.SetGridCursor(row, col)
                            self.MakeCellVisible(row, col)
                            return
                    except IndexError:
                        return
                startcol = 0
                row += 1
        else:
            while True:
                for col in xrange(startcol, -1, -1):
                    try:
                        foo = self.table.GetValue(row, col)
                        text = self._getvalue(row, col)
                        if searchtext in text.string().lower():
                            self.SetGridCursor(row, col)
                            self.MakeCellVisible(row, col)
                            return
                    except IndexError:
                        return
                startcol = self.table.GetNumberCols()-1
                row -= 1

    def key_pressed(self, event):
        """
        Maps pressed keys to functions
        """
        frame = self.GetParent().GetParent().GetParent()
        frame.SetStatusText("")
        sh = event.ShiftDown()
        ctrl = event.ControlDown()

        keycode = event.GetKeyCode()
        if keycode == ord("P"):
            row = self.GetGridCursorRow()
            if event.ShiftDown():
                col = self.GetGridCursorCol()
                self.pickattr(row, col)
            else:
                self.pick(row)
        elif keycode == ord("M"):
            if ctrl:
                col = self.GetGridCursorCol()
                self.pickrowsattr(sorted(self.current_selection), col)
            else:
                self.pickrows(sorted(self.current_selection))
        elif keycode in (wx.WXK_BACK, wx.WXK_DELETE, ord("X")) and not (ctrl or sh):
            self.delete_current_notebook()
        elif keycode == ord("E") and not (ctrl or sh):
            row = self.GetGridCursorRow()
            self.enter(row)
        elif keycode == ord("E") and sh and not ctrl:
            row = self.GetGridCursorRow()
            col = self.GetGridCursorCol()
            self.enterattr(row, col)
        elif keycode == ord("E") and ctrl:
            row = self.GetGridCursorRow()
            self.SetGridCursor(row, self.GetNumberCols()-1)
        elif keycode == wx.WXK_HOME or (keycode == ord("A") and ctrl):
            row = self.GetGridCursorRow()
            self.SetGridCursor(row, 0)
        elif keycode == ord("C") and sh:
            col = self.GetGridCursorCol()
            attr = self.table._displayattrs[col]
            returnobj = []
            for i in xrange(self.GetNumberRows()):
                returnobj.append(self.table._displayattrs[col].value(self.table.items[i]))
            self.quit(returnobj)
        elif keycode in (wx.WXK_ESCAPE, ord("Q")) and not (ctrl or sh):
            self.quit()
        elif keycode == ord("<"):
            row = self.GetGridCursorRow()
            col = self.GetGridCursorCol()
            if not event.ShiftDown():
                newcol = col - 1
                if newcol >= 0:
                    self.SetGridCursor(row, col - 1)
            else:
                newcol = col + 1
                if newcol < self.GetNumberCols():
                    self.SetGridCursor(row, col + 1)
        elif keycode == ord("D"):
            col = self.GetGridCursorCol()
            row = self.GetGridCursorRow()
            if not sh:
                self.detail(row, col)
            else:
                self.detail_attr(row, col)
        elif keycode == ord("F") and ctrl:
            frame.enter_searchtext(event)
        elif keycode == wx.WXK_F3:
            if sh:
                frame.find_previous(event)
            else:
                frame.find_next(event)
        elif keycode == ord("V"):
            if sh:
                self.sortattrdesc()
            else:
                self.sortattrasc()
        elif keycode == wx.WXK_DOWN:
            row = self.GetGridCursorRow()
            try:
                item = self.table.items[row+1]
            except IndexError:
                item = self.table.items[row]
            self.set_footer(item)
            event.Skip()
        elif keycode == wx.WXK_UP:
            row = self.GetGridCursorRow()
            if row >= 1:
                item = self.table.items[row-1]
            else:
                item = self.table.items[row]
            self.set_footer(item)
            event.Skip()         
        elif keycode == wx.WXK_RIGHT:
            row = self.GetGridCursorRow()
            item = self.table.items[row]
            self.set_footer(item)
            event.Skip()
        elif keycode == wx.WXK_LEFT:
            row = self.GetGridCursorRow()
            item = self.table.items[row]
            self.set_footer(item)
            event.Skip()
        else:
            event.Skip()

    def delete_current_notebook(self):
        """
        deletes the current notebook tab
        """
        panel = self.GetParent()
        nb = panel.GetParent()
        current = nb.GetSelection()
        count = nb.GetPageCount()
        if count > 1:
            for i in xrange(count-1, current-1, -1):
                nb.DeletePage(i)
            nb.GetCurrentPage().grid.SetFocus()
        else:
            frame = nb.GetParent()
            frame.SetStatusText("This is the last level!")

    def _doenter(self, value, *attrs):
        """
        "enter" a special item resulting in a new notebook tab
        """
        panel = self.GetParent()
        nb = panel.GetParent()
        frame = nb.GetParent()
        current = nb.GetSelection()
        count = nb.GetPageCount()
        try: # if we want to enter something non-iterable, e.g. a function
            if current + 1 == count and value is not self.input: # we have an event in the last tab
                frame._add_notebook(value, *attrs)
            elif value != self.input: # we have to delete all tabs newer than [panel] first
                for i in xrange(count-1, current, -1): # some tabs don't close if we don't close in *reverse* order
                    nb.DeletePage(i)
                frame._add_notebook(value)
        except TypeError, exc:
            if exc.__class__.__module__ == "exceptions":
                msg = "%s: %s" % (exc.__class__.__name__, exc)
            else:
                msg = "%s.%s: %s" % (exc.__class__.__module__, exc.__class__.__name__, exc)
            frame.SetStatusText(msg)

    def enterattr(self, row, col):
        try:
            attr = self.table._displayattrs[col]
            value = attr.value(self.table.items[row])
        except Exception, exc:
            self.error_output(str(exc))
        else:
            self._doenter(value)

    def set_footer(self, item):
        frame = self.GetParent().GetParent().GetParent()
        frame.SetStatusText(" ".join([str(text) for (style, text) in ipipe.xformat(item, "footer", 20)[2]]))

    def enter(self, row):
        try:
            value = self.table.items[row]
        except Exception, exc:
            self.error_output(str(exc))
        else:
            self._doenter(value)

    def detail(self, row, col):
        """
        shows a detail-view of the current cell
        """
        try:
            attr = self.table._displayattrs[col]
            item = self.table.items[row]
        except Exception, exc:
            self.error_output(str(exc))
        else:
            attrs = [ipipe.AttributeDetail(item, attr) for attr in ipipe.xattrs(item, "detail")]
            self._doenter(attrs)

    def detail_attr(self, row, col):
        try:
            attr = self.table._displayattrs[col]
            item = attr.value(self.table.items[row])
        except Exception, exc:
            self.error_output(str(exc))
        else:
            attrs = [ipipe.AttributeDetail(item, attr) for attr in ipipe.xattrs(item, "detail")]
            self._doenter(attrs)

    def quit(self, returnobj=None):
        """
        quit
        """
        frame = self.GetParent().GetParent().GetParent()
        if frame.helpdialog:
            frame.helpdialog.Destroy()
        frame.parent.returnobj = returnobj
        frame.Close()
        frame.Destroy()

    def cell_doubleclicked(self, event):
        self.enterattr(event.GetRow(), event.GetCol())
        event.Skip()

    def cell_leftclicked(self, event):
        row = event.GetRow()
        item = self.table.items[row]
        self.set_footer(item)
        event.Skip()
        
    def pick(self, row):
        """
        pick a single row and return to the IPython prompt
        """
        try:
            value = self.table.items[row]
        except Exception, exc:
            self.error_output(str(exc))
        else:
            self.quit(value)

    def pickrows(self, rows):
        """
        pick multiple rows and return to the IPython prompt
        """
        try:
            value = [self.table.items[row] for row in rows]
        except Exception, exc:
            self.error_output(str(exc))
        else:
            self.quit(value)

    def pickrowsattr(self, rows, col):
        """"
        pick one column from multiple rows
        """
        values = []
        try:
            attr = self.table._displayattrs[col]
            for row in rows:
                try:
                    values.append(attr.value(self.table.items[row]))
                except (SystemExit, KeyboardInterrupt):
                    raise
                except Exception:
                    raise #pass
        except Exception, exc:
            self.error_output(str(exc))
        else:
            self.quit(values)

    def pickattr(self, row, col):
        try:
            attr = self.table._displayattrs[col]
            value = attr.value(self.table.items[row])
        except Exception, exc:
            self.error_output(str(exc))
        else:
            self.quit(value)


class IGridPanel(wx.Panel):
    # Each IGridPanel contains an IGridGrid
    def __init__(self, parent, input, *attrs):
        wx.Panel.__init__(self, parent, -1)
        self.grid = IGridGrid(self, input, *attrs)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.grid, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        self.SetSizer(sizer)
        sizer.Fit(self)
        sizer.SetSizeHints(self)


class IGridHTMLHelp(wx.Frame):
    def __init__(self, parent, title, filename, size):
        wx.Frame.__init__(self, parent, -1, title, size=size)
        html = wx.html.HtmlWindow(self)
        if "gtk2" in wx.PlatformInfo:
            html.SetStandardFonts()
        html.LoadFile(filename)


class IGridFrame(wx.Frame):
    maxtitlelen = 30

    def __init__(self, parent, input):
        title =  " ".join([str(x[1]) for x in ipipe.xformat(input, "header", 20)[2]])
        wx.Frame.__init__(self, None, title=title, size=(640, 480))
        self.menubar = wx.MenuBar()
        self.menucounter = 100
        self.m_help = wx.Menu()
        self.m_search = wx.Menu()
        self.m_sort = wx.Menu()
        self.notebook = wx.Notebook(self, -1, style=0)
        self.statusbar = self.CreateStatusBar(1, wx.ST_SIZEGRIP)
        self.parent = parent
        self._add_notebook(input)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.makemenu(self.m_sort, "&Sort (asc)", "Sort ascending", self.sortasc)
        self.makemenu(self.m_sort, "Sort (&desc)", "Sort descending", self.sortdesc)
        self.makemenu(self.m_help, "&Help", "Help", self.display_help)
        self.makemenu(self.m_help, "&Show help in browser", "Show help in browser", self.display_help_in_browser)
        self.makemenu(self.m_search, "&Find text", "Find text", self.enter_searchtext)
        self.makemenu(self.m_search, "Find by &expression", "Find by expression", self.enter_searchexpression)
        self.makemenu(self.m_search, "Find &next", "Find next", self.find_next)
        self.makemenu(self.m_search, "Find &previous", "Find previous", self.find_previous)
        self.menubar.Append(self.m_search, "&Find")
        self.menubar.Append(self.m_sort, "&Sort")
        self.menubar.Append(self.m_help, "&Help")
        self.SetMenuBar(self.menubar)
        self.searchtext = ""
        self.helpdialog = None

    def sortasc(self, event):
        grid = self.notebook.GetPage(self.notebook.GetSelection()).grid
        grid.sortattrasc()

    def sortdesc(self, event):
        grid = self.notebook.GetPage(self.notebook.GetSelection()).grid
        grid.sortattrdesc()

    def find_previous(self, event):
        """
        find previous occurrences
        """
        if self.searchtext:
            grid = self.notebook.GetPage(self.notebook.GetSelection()).grid
            row = grid.GetGridCursorRow()
            col = grid.GetGridCursorCol()
            if col-1 >= 0:
                grid.search(self.searchtext, row, col-1, False)
            else:
                grid.search(self.searchtext, row-1, grid.table.GetNumberCols()-1, False)
        else:
            self.enter_searchtext(event)

    def find_next(self, event):
        """
        find the next occurrence
        """
        if self.searchtext:
            grid = self.notebook.GetPage(self.notebook.GetSelection()).grid
            row = grid.GetGridCursorRow()
            col = grid.GetGridCursorCol()
            if col+1 < grid.table.GetNumberCols():
                grid.search(self.searchtext, row, col+1)
            else:
                grid.search(self.searchtext, row+1, 0)
        else:
            self.enter_searchtext(event)

    def display_help(self, event):
        """
        Display a help dialog
        """
        if self.helpdialog:
            self.helpdialog.Destroy()
        filename = os.path.join(os.path.dirname(__file__), "igrid_help.html")
        self.helpdialog = IGridHTMLHelp(None, title="Help", filename=filename, size=wx.Size(600,400))
        self.helpdialog.Show()

    def display_help_in_browser(self, event):
        """
        Show the help-HTML in a browser (as a ``HtmlWindow`` does not understand
        CSS this looks better)
        """
        filename = urllib.pathname2url(os.path.abspath(os.path.join(os.path.dirname(__file__), "igrid_help.html")))
        if not filename.startswith("file"):
            filename = "file:" + filename
        webbrowser.open(filename, new=1, autoraise=True)

    def enter_searchexpression(self, event):
        pass

    def makemenu(self, menu, label, help, cmd):
        menu.Append(self.menucounter, label, help)
        self.Bind(wx.EVT_MENU, cmd, id=self.menucounter)
        self.menucounter += 1

    def _add_notebook(self, input, *attrs):
        # Adds another notebook which has the starting object ``input``
        panel = IGridPanel(self.notebook, input, *attrs)
        text = str(ipipe.xformat(input, "header", self.maxtitlelen)[2])
        if len(text) >= self.maxtitlelen:
            text = text[:self.maxtitlelen].rstrip(".") + "..."
        self.notebook.AddPage(panel, text, True)
        panel.grid.SetFocus()
        self.Layout()

    def OnCloseWindow(self, event):
        self.Destroy()

    def enter_searchtext(self, event):
        # Displays a dialog asking for the searchtext
        dlg = wx.TextEntryDialog(self, "Find:", "Find in list")
        if dlg.ShowModal() == wx.ID_OK:
            self.searchtext = dlg.GetValue()
            self.notebook.GetPage(self.notebook.GetSelection()).grid.search(self.searchtext, 0, 0)
        dlg.Destroy()


class igrid(ipipe.Display):
    """
    This is a wx-based display object that can be used instead of ``ibrowse``
    (which is curses-based) or ``idump`` (which simply does a print).
    """
    def display(self):
        self.returnobj = None
        app = wx.App()
        self.frame = IGridFrame(self, self.input)
        self.frame.Show()
        app.SetTopWindow(self.frame)
        self.frame.Raise()
        app.MainLoop()
        return self.returnobj
