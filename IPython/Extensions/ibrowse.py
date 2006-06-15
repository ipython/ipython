# -*- coding: iso-8859-1 -*-

import curses, textwrap

import astyle, ipipe


_ibrowse_help = """
down
Move the cursor to the next line.

up
Move the cursor to the previous line.

pagedown
Move the cursor down one page (minus overlap).

pageup
Move the cursor up one page (minus overlap).

left
Move the cursor left.

right
Move the cursor right.

home
Move the cursor to the first column.

end
Move the cursor to the last column.

prevattr
Move the cursor one attribute column to the left.

nextattr
Move the cursor one attribute column to the right.

pick
'Pick' the object under the cursor (i.e. the row the cursor is on). This
leaves the browser and returns the picked object to the caller. (In IPython
this object will be available as the '_' variable.)

pickattr
'Pick' the attribute under the cursor (i.e. the row/column the cursor is on).

pickallattrs
Pick' the complete column under the cursor (i.e. the attribute under the
cursor) from all currently fetched objects. These attributes will be returned
as a list.

tooglemark
Mark/unmark the object under the cursor. Marked objects have a '!' after the
row number).

pickmarked
'Pick' marked objects. Marked objects will be returned as a list.

pickmarkedattr
'Pick' the attribute under the cursor from all marked objects (This returns a
list).

enterdefault
Enter the object under the cursor. (what this mean depends on the object
itself (i.e. how it implements the '__xiter__' method). This opens a new
browser 'level'.

enter
Enter the object under the cursor. If the object provides different enter
modes a menu of all modes will be presented; choose one and enter it (via the
'enter' or 'enterdefault' command).

enterattr
Enter the attribute under the cursor.

leave
Leave the current browser level and go back to the previous one.

detail
Show a detail view of the object under the cursor. This shows the name, type,
doc string and value of the object attributes (and it might show more
attributes than in the list view, depending on the object).

detailattr
Show a detail view of the attribute under the cursor.

markrange
Mark all objects from the last marked object before the current cursor
position to the cursor position.

sortattrasc
Sort the objects (in ascending order) using the attribute under the cursor as
the sort key.

sortattrdesc
Sort the objects (in descending order) using the attribute under the cursor as
the sort key.

goto
Jump to a row. The row number can be entered at the bottom of the screen.

find
Search forward for a row. At the bottom of the screen the condition can be
entered.

findbackwards
Search backward for a row. At the bottom of the screen the condition can be
entered.

help
This screen.
"""


class UnassignedKeyError(Exception):
    """
    Exception that is used for reporting unassigned keys.
    """


class UnknownCommandError(Exception):
    """
    Exception that is used for reporting unknown command (this should never
    happen).
    """


class CommandError(Exception):
    """
    Exception that is used for reporting that a command can't be executed.
    """


class _BrowserCachedItem(object):
    # This is used internally by ``ibrowse`` to store a item together with its
    # marked status.
    __slots__ = ("item", "marked")

    def __init__(self, item):
        self.item = item
        self.marked = False


class _BrowserHelp(object):
    style_header = astyle.Style.fromstr("red:blacK")
    # This is used internally by ``ibrowse`` for displaying the help screen.
    def __init__(self, browser):
        self.browser = browser

    def __xrepr__(self, mode):
        yield (-1, True)
        if mode == "header" or mode == "footer":
            yield (astyle.style_default, "ibrowse help screen")
        else:
            yield (astyle.style_default, repr(self))

    def __xiter__(self, mode):
        # Get reverse key mapping
        allkeys = {}
        for (key, cmd) in self.browser.keymap.iteritems():
            allkeys.setdefault(cmd, []).append(key)

        fields = ("key", "description")

        for (i, command) in enumerate(_ibrowse_help.strip().split("\n\n")):
            if i:
                yield ipipe.Fields(fields, key="", description="")

            (name, description) = command.split("\n", 1)
            keys = allkeys.get(name, [])
            lines = textwrap.wrap(description, 60)

            yield ipipe.Fields(fields, description=astyle.Text((self.style_header, name)))
            for i in xrange(max(len(keys), len(lines))):
                try:
                    key = self.browser.keylabel(keys[i])
                except IndexError:
                    key = ""
                try:
                    line = lines[i]
                except IndexError:
                    line = ""
                yield ipipe.Fields(fields, key=key, description=line)


class _BrowserLevel(object):
    # This is used internally to store the state (iterator, fetch items,
    # position of cursor and screen, etc.) of one browser level
    # An ``ibrowse`` object keeps multiple ``_BrowserLevel`` objects in
    # a stack.
    def __init__(self, browser, input, iterator, mainsizey, *attrs):
        self.browser = browser
        self.input = input
        self.header = [x for x in ipipe.xrepr(input, "header") if not isinstance(x[0], int)]
        # iterator for the input
        self.iterator = iterator

        # is the iterator exhausted?
        self.exhausted = False

        # attributes to be display (autodetected if empty)
        self.attrs = attrs

        # fetched items (+ marked flag)
        self.items = ipipe.deque()

        # Number of marked objects
        self.marked = 0

        # Vertical cursor position
        self.cury = 0

        # Horizontal cursor position
        self.curx = 0

        # Index of first data column
        self.datastartx = 0

        # Index of first data line
        self.datastarty = 0

        # height of the data display area
        self.mainsizey = mainsizey

        # width of the data display area (changes when scrolling)
        self.mainsizex = 0

        # Size of row number (changes when scrolling)
        self.numbersizex = 0

        # Attribute names to display (in this order)
        self.displayattrs = []

        # index and name of attribute under the cursor
        self.displayattr = (None, ipipe.noitem)

        # Maps attribute names to column widths
        self.colwidths = {}

        # This takes care of all the caches etc.
        self.moveto(0, 0, refresh=True)

    def fetch(self, count):
        # Try to fill ``self.items`` with at least ``count`` objects.
        have = len(self.items)
        while not self.exhausted and have < count:
            try:
                item = self.iterator.next()
            except StopIteration:
                self.exhausted = True
                break
            else:
                have += 1
                self.items.append(_BrowserCachedItem(item))

    def calcdisplayattrs(self):
        # Calculate which attributes are available from the objects that are
        # currently visible on screen (and store it in ``self.displayattrs``)
        attrnames = set()
        # If the browser object specifies a fixed list of attributes,
        # simply use it.
        if self.attrs:
            self.displayattrs = self.attrs
        else:
            self.displayattrs = []
            endy = min(self.datastarty+self.mainsizey, len(self.items))
            for i in xrange(self.datastarty, endy):
                for attrname in ipipe.xattrs(self.items[i].item, "default"):
                    if attrname not in attrnames:
                        self.displayattrs.append(attrname)
                        attrnames.add(attrname)

    def getrow(self, i):
        # Return a dictinary with the attributes for the object
        # ``self.items[i]``. Attribute names are taken from
        # ``self.displayattrs`` so ``calcdisplayattrs()`` must have been
        # called before.
        row = {}
        item = self.items[i].item
        for attrname in self.displayattrs:
            try:
                value = ipipe._getattr(item, attrname, ipipe.noitem)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception, exc:
                value = exc
            # only store attribute if it exists (or we got an exception)
            if value is not ipipe.noitem:
                # remember alignment, length and colored text
                row[attrname] = ipipe.xformat(value, "cell", self.browser.maxattrlength)
        return row

    def calcwidths(self):
        # Recalculate the displayed fields and their widths.
        # ``calcdisplayattrs()'' must have been called and the cache
        # for attributes of the objects on screen (``self.displayrows``)
        # must have been filled. This returns a dictionary mapping
        # column names to widths.
        self.colwidths = {}
        for row in self.displayrows:
            for attrname in self.displayattrs:
                try:
                    length = row[attrname][1]
                except KeyError:
                    length = 0
                # always add attribute to colwidths, even if it doesn't exist
                if attrname not in self.colwidths:
                    self.colwidths[attrname] = len(ipipe._attrname(attrname))
                newwidth = max(self.colwidths[attrname], length)
                self.colwidths[attrname] = newwidth

        # How many characters do we need to paint the largest item number?
        self.numbersizex = len(str(self.datastarty+self.mainsizey-1))
        # How must space have we got to display data?
        self.mainsizex = self.browser.scrsizex-self.numbersizex-3
        # width of all columns
        self.datasizex = sum(self.colwidths.itervalues()) + len(self.colwidths)

    def calcdisplayattr(self):
        # Find out which attribute the cursor is on and store this
        # information in ``self.displayattr``.
        pos = 0
        for (i, attrname) in enumerate(self.displayattrs):
            if pos+self.colwidths[attrname] >= self.curx:
                self.displayattr = (i, attrname)
                break
            pos += self.colwidths[attrname]+1
        else:
            self.displayattr = (None, ipipe.noitem)

    def moveto(self, x, y, refresh=False):
        # Move the cursor to the position ``(x,y)`` (in data coordinates,
        # not in screen coordinates). If ``refresh`` is true, all cached
        # values will be recalculated (e.g. because the list has been
        # resorted, so screen positions etc. are no longer valid).
        olddatastarty = self.datastarty
        oldx = self.curx
        oldy = self.cury
        x = int(x+0.5)
        y = int(y+0.5)
        newx = x # remember where we wanted to move
        newy = y # remember where we wanted to move

        scrollbordery = min(self.browser.scrollbordery, self.mainsizey//2)
        scrollborderx = min(self.browser.scrollborderx, self.mainsizex//2)

        # Make sure that the cursor didn't leave the main area vertically
        if y < 0:
            y = 0
        # try to get enough items to fill the screen
        self.fetch(max(y+scrollbordery+1, self.mainsizey))
        if y >= len(self.items):
            y = max(0, len(self.items)-1)

        # Make sure that the cursor stays on screen vertically
        if y < self.datastarty+scrollbordery:
            self.datastarty = max(0, y-scrollbordery)
        elif y >= self.datastarty+self.mainsizey-scrollbordery:
            self.datastarty = max(0, min(y-self.mainsizey+scrollbordery+1,
                                         len(self.items)-self.mainsizey))

        if refresh: # Do we need to refresh the complete display?
            self.calcdisplayattrs()
            endy = min(self.datastarty+self.mainsizey, len(self.items))
            self.displayrows = map(self.getrow, xrange(self.datastarty, endy))
            self.calcwidths()
        # Did we scroll vertically => update displayrows
        # and various other attributes
        elif self.datastarty != olddatastarty:
            # Recalculate which attributes we have to display
            olddisplayattrs = self.displayattrs
            self.calcdisplayattrs()
            # If there are new attributes, recreate the cache
            if self.displayattrs != olddisplayattrs:
                endy = min(self.datastarty+self.mainsizey, len(self.items))
                self.displayrows = map(self.getrow, xrange(self.datastarty, endy))
            elif self.datastarty<olddatastarty: # we did scroll up
                # drop rows from the end
                del self.displayrows[self.datastarty-olddatastarty:]
                # fetch new items
                for i in xrange(olddatastarty-1,
                                self.datastarty-1, -1):
                    try:
                        row = self.getrow(i)
                    except IndexError:
                        # we didn't have enough objects to fill the screen
                        break
                    self.displayrows.insert(0, row)
            else: # we did scroll down
                # drop rows from the start
                del self.displayrows[:self.datastarty-olddatastarty]
                # fetch new items
                for i in xrange(olddatastarty+self.mainsizey,
                                self.datastarty+self.mainsizey):
                    try:
                        row = self.getrow(i)
                    except IndexError:
                        # we didn't have enough objects to fill the screen
                        break
                    self.displayrows.append(row)
            self.calcwidths()

        # Make sure that the cursor didn't leave the data area horizontally
        if x < 0:
            x = 0
        elif x >= self.datasizex:
            x = max(0, self.datasizex-1)

        # Make sure that the cursor stays on screen horizontally
        if x < self.datastartx+scrollborderx:
            self.datastartx = max(0, x-scrollborderx)
        elif x >= self.datastartx+self.mainsizex-scrollborderx:
            self.datastartx = max(0, min(x-self.mainsizex+scrollborderx+1,
                                         self.datasizex-self.mainsizex))

        if x == oldx and y == oldy and (x != newx or y != newy): # couldn't move
            self.browser.beep()
        else:
            self.curx = x
            self.cury = y
            self.calcdisplayattr()

    def sort(self, key, reverse=False):
        """
        Sort the currently list of items using the key function ``key``. If
        ``reverse`` is true the sort order is reversed.
        """
        curitem = self.items[self.cury] # Remember where the cursor is now

        # Sort items
        def realkey(item):
            return key(item.item)
        self.items = ipipe.deque(sorted(self.items, key=realkey, reverse=reverse))

        # Find out where the object under the cursor went
        cury = self.cury
        for (i, item) in enumerate(self.items):
            if item is curitem:
                cury = i
                break

        self.moveto(self.curx, cury, refresh=True)


class _CommandInput(object):
    keymap = {
        curses.KEY_LEFT: "left",
        curses.KEY_RIGHT: "right",
        curses.KEY_HOME: "home",
        curses.KEY_END: "end",
        # FIXME: What's happening here?
        8: "backspace",
        127: "backspace",
        curses.KEY_BACKSPACE: "backspace",
        curses.KEY_DC: "delete",
        ord("x"): "delete",
        ord("\n"): "execute",
        ord("\r"): "execute",
        curses.KEY_UP: "up",
        curses.KEY_DOWN: "down",
        # CTRL-X
        0x18: "exit",
    }

    def __init__(self, prompt):
        self.prompt = prompt
        self.history = []
        self.maxhistory = 100
        self.input = ""
        self.curx = 0
        self.cury = -1 # blank line

    def start(self):
        self.input = ""
        self.curx = 0
        self.cury = -1 # blank line

    def handlekey(self, browser, key):
        cmdname = self.keymap.get(key, None)
        if cmdname is not None:
            cmdfunc = getattr(self, "cmd_%s" % cmdname, None)
            if cmdfunc is not None:
                return cmdfunc(browser)
            curses.beep()
        elif key != -1:
            try:
                char = chr(key)
            except ValueError:
                curses.beep()
            else:
                return self.handlechar(browser, char)

    def handlechar(self, browser, char):
        self.input = self.input[:self.curx] + char + self.input[self.curx:]
        self.curx += 1
        return True

    def dohistory(self):
        self.history.insert(0, self.input)
        del self.history[:-self.maxhistory]

    def cmd_backspace(self, browser):
        if self.curx:
            self.input = self.input[:self.curx-1] + self.input[self.curx:]
            self.curx -= 1
            return True
        else:
            curses.beep()

    def cmd_delete(self, browser):
        if self.curx<len(self.input):
            self.input = self.input[:self.curx] + self.input[self.curx+1:]
            return True
        else:
            curses.beep()

    def cmd_left(self, browser):
        if self.curx:
            self.curx -= 1
            return True
        else:
            curses.beep()

    def cmd_right(self, browser):
        if self.curx < len(self.input):
            self.curx += 1
            return True
        else:
            curses.beep()

    def cmd_home(self, browser):
        if self.curx:
            self.curx = 0
            return True
        else:
            curses.beep()

    def cmd_end(self, browser):
        if self.curx < len(self.input):
            self.curx = len(self.input)
            return True
        else:
            curses.beep()

    def cmd_up(self, browser):
        if self.cury < len(self.history)-1:
            self.cury += 1
            self.input = self.history[self.cury]
            self.curx = len(self.input)
            return True
        else:
            curses.beep()

    def cmd_down(self, browser):
        if self.cury >= 0:
            self.cury -= 1
            if self.cury>=0:
                self.input = self.history[self.cury]
            else:
                self.input = ""
            self.curx = len(self.input)
            return True
        else:
            curses.beep()

    def cmd_exit(self, browser):
        browser.mode = "default"
        return True

    def cmd_execute(self, browser):
        raise NotImplementedError


class _CommandGoto(_CommandInput):
    def __init__(self):
        _CommandInput.__init__(self, "goto object #")

    def handlechar(self, browser, char):
        # Only accept digits
        if not "0" <= char <= "9":
            curses.beep()
        else:
            return _CommandInput.handlechar(self, browser, char)

    def cmd_execute(self, browser):
        level = browser.levels[-1]
        if self.input:
            self.dohistory()
            level.moveto(level.curx, int(self.input))
        browser.mode = "default"
        return True


class _CommandFind(_CommandInput):
    def __init__(self):
        _CommandInput.__init__(self, "find expression")

    def cmd_execute(self, browser):
        level = browser.levels[-1]
        if self.input:
            self.dohistory()
            while True:
                cury = level.cury
                level.moveto(level.curx, cury+1)
                if cury == level.cury:
                    curses.beep()
                    break # hit end
                item = level.items[level.cury].item
                try:
                    globals = ipipe.getglobals(None)
                    if eval(self.input, globals, ipipe.AttrNamespace(item)):
                        break # found something
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception, exc:
                    browser.report(exc)
                    curses.beep()
                    break  # break on error
        browser.mode = "default"
        return True


class _CommandFindBackwards(_CommandInput):
    def __init__(self):
        _CommandInput.__init__(self, "find backwards expression")

    def cmd_execute(self, browser):
        level = browser.levels[-1]
        if self.input:
            self.dohistory()
            while level.cury:
                level.moveto(level.curx, level.cury-1)
                item = level.items[level.cury].item
                try:
                    globals = ipipe.getglobals(None)
                    if eval(self.input, globals, ipipe.AttrNamespace(item)):
                        break # found something
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception, exc:
                    browser.report(exc)
                    curses.beep()
                    break # break on error
            else:
                curses.beep()
        browser.mode = "default"
        return True


class ibrowse(ipipe.Display):
    # Show this many lines from the previous screen when paging horizontally
    pageoverlapx = 1

    # Show this many lines from the previous screen when paging vertically
    pageoverlapy = 1

    # Start scrolling when the cursor is less than this number of columns
    # away from the left or right screen edge
    scrollborderx = 10

    # Start scrolling when the cursor is less than this number of lines
    # away from the top or bottom screen edge
    scrollbordery = 5

    # Accelerate by this factor when scrolling horizontally
    acceleratex = 1.05

    # Accelerate by this factor when scrolling vertically
    acceleratey = 1.05

    # The maximum horizontal scroll speed
    # (as a factor of the screen width (i.e. 0.5 == half a screen width)
    maxspeedx = 0.5

    # The maximum vertical scroll speed
    # (as a factor of the screen height (i.e. 0.5 == half a screen height)
    maxspeedy = 0.5

    # The maximum number of header lines for browser level
    # if the nesting is deeper, only the innermost levels are displayed
    maxheaders = 5

    # The approximate maximum length of a column entry
    maxattrlength = 200

    # Styles for various parts of the GUI
    style_objheadertext = astyle.Style.fromstr("white:black:bold|reverse")
    style_objheadernumber = astyle.Style.fromstr("white:blue:bold|reverse")
    style_objheaderobject = astyle.Style.fromstr("white:black:reverse")
    style_colheader = astyle.Style.fromstr("blue:white:reverse")
    style_colheaderhere = astyle.Style.fromstr("green:black:bold|reverse")
    style_colheadersep = astyle.Style.fromstr("blue:black:reverse")
    style_number = astyle.Style.fromstr("blue:white:reverse")
    style_numberhere = astyle.Style.fromstr("green:black:bold|reverse")
    style_sep = astyle.Style.fromstr("blue:black")
    style_data = astyle.Style.fromstr("white:black")
    style_datapad = astyle.Style.fromstr("blue:black:bold")
    style_footer = astyle.Style.fromstr("black:white")
    style_report = astyle.Style.fromstr("white:black")

    # Column separator in header
    headersepchar = "|"

    # Character for padding data cell entries
    datapadchar = "."

    # Column separator in data area
    datasepchar = "|"

    # Character to use for "empty" cell (i.e. for non-existing attributes)
    nodatachar = "-"

    # Prompts for modes that require keyboard input
    prompts = {
        "goto": _CommandGoto(),
        "find": _CommandFind(),
        "findbackwards": _CommandFindBackwards()
    }

    # Maps curses key codes to "function" names
    keymap = {
        ord("q"): "quit",
        curses.KEY_UP: "up",
        curses.KEY_DOWN: "down",
        curses.KEY_PPAGE: "pageup",
        curses.KEY_NPAGE: "pagedown",
        curses.KEY_LEFT: "left",
        curses.KEY_RIGHT: "right",
        curses.KEY_HOME: "home",
        curses.KEY_END: "end",
        ord("<"): "prevattr",
        0x1b:     "prevattr", # SHIFT-TAB
        ord(">"): "nextattr",
        ord("\t"):"nextattr", # TAB
        ord("p"): "pick",
        ord("P"): "pickattr",
        ord("C"): "pickallattrs",
        ord("m"): "pickmarked",
        ord("M"): "pickmarkedattr",
        ord("\n"): "enterdefault",
        ord("\r"): "enterdefault",
        # FIXME: What's happening here?
        8: "leave",
        127: "leave",
        curses.KEY_BACKSPACE: "leave",
        ord("x"): "leave",
        ord("h"): "help",
        ord("e"): "enter",
        ord("E"): "enterattr",
        ord("d"): "detail",
        ord("D"): "detailattr",
        ord(" "): "tooglemark",
        ord("r"): "markrange",
        ord("v"): "sortattrasc",
        ord("V"): "sortattrdesc",
        ord("g"): "goto",
        ord("f"): "find",
        ord("b"): "findbackwards",
    }

    def __init__(self, *attrs):
        """
        Create a new browser. If ``attrs`` is not empty, it is the list
        of attributes that will be displayed in the browser, otherwise
        these will be determined by the objects on screen.
        """
        self.attrs = attrs

        # Stack of browser levels
        self.levels = []
        # how many colums to scroll (Changes when accelerating)
        self.stepx = 1.

        # how many rows to scroll (Changes when accelerating)
        self.stepy = 1.

        # Beep on the edges of the data area? (Will be set to ``False``
        # once the cursor hits the edge of the screen, so we don't get
        # multiple beeps).
        self._dobeep = True

        # Cache for registered ``curses`` colors and styles.
        self._styles = {}
        self._colors = {}
        self._maxcolor = 1

        # How many header lines do we want to paint (the numbers of levels
        # we have, but with an upper bound)
        self._headerlines = 1

        # Index of first header line
        self._firstheaderline = 0

        # curses window
        self.scr = None
        # report in the footer line (error, executed command etc.)
        self._report = None

        # value to be returned to the caller (set by commands)
        self.returnvalue = None

        # The mode the browser is in
        # e.g. normal browsing or entering an argument for a command
        self.mode = "default"

    def nextstepx(self, step):
        """
        Accelerate horizontally.
        """
        return max(1., min(step*self.acceleratex,
                           self.maxspeedx*self.levels[-1].mainsizex))

    def nextstepy(self, step):
        """
        Accelerate vertically.
        """
        return max(1., min(step*self.acceleratey,
                           self.maxspeedy*self.levels[-1].mainsizey))

    def getstyle(self, style):
        """
        Register the ``style`` with ``curses`` or get it from the cache,
        if it has been registered before.
        """
        try:
            return self._styles[style.fg, style.bg, style.attrs]
        except KeyError:
            attrs = 0
            for b in astyle.A2CURSES:
                if style.attrs & b:
                    attrs |= astyle.A2CURSES[b]
            try:
                color = self._colors[style.fg, style.bg]
            except KeyError:
                curses.init_pair(
                    self._maxcolor,
                    astyle.COLOR2CURSES[style.fg],
                    astyle.COLOR2CURSES[style.bg]
                )
                color = curses.color_pair(self._maxcolor)
                self._colors[style.fg, style.bg] = color
                self._maxcolor += 1
            c = color | attrs
            self._styles[style.fg, style.bg, style.attrs] = c
            return c

    def addstr(self, y, x, begx, endx, text, style):
        """
        A version of ``curses.addstr()`` that can handle ``x`` coordinates
        that are outside the screen.
        """
        text2 = text[max(0, begx-x):max(0, endx-x)]
        if text2:
            self.scr.addstr(y, max(x, begx), text2, self.getstyle(style))
        return len(text)

    def addchr(self, y, x, begx, endx, c, l, style):
        x0 = max(x, begx)
        x1 = min(x+l, endx)
        if x1>x0:
            self.scr.addstr(y, x0, c*(x1-x0), self.getstyle(style))
        return l

    def _calcheaderlines(self, levels):
        # Calculate how many headerlines do we have to display, if we have
        # ``levels`` browser levels
        if levels is None:
            levels = len(self.levels)
        self._headerlines = min(self.maxheaders, levels)
        self._firstheaderline = levels-self._headerlines

    def getstylehere(self, style):
        """
        Return a style for displaying the original style ``style``
        in the row the cursor is on.
        """
        return astyle.Style(style.fg, style.bg, style.attrs | astyle.A_BOLD)

    def report(self, msg):
        """
        Store the message ``msg`` for display below the footer line. This
        will be displayed as soon as the screen is redrawn.
        """
        self._report = msg

    def enter(self, item, mode, *attrs):
        """
        Enter the object ``item`` in the mode ``mode``. If ``attrs`` is
        specified, it will be used as a fixed list of attributes to display.
        """
        try:
            iterator = ipipe.xiter(item, mode)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, exc:
            curses.beep()
            self.report(exc)
        else:
            self._calcheaderlines(len(self.levels)+1)
            level = _BrowserLevel(
                self,
                item,
                iterator,
                self.scrsizey-1-self._headerlines-2,
                *attrs
            )
            self.levels.append(level)

    def startkeyboardinput(self, mode):
        """
        Enter mode ``mode``, which requires keyboard input.
        """
        self.mode = mode
        self.prompts[mode].start()

    def keylabel(self, keycode):
        """
        Return a pretty name for the ``curses`` key ``keycode`` (used in the
        help screen and in reports about unassigned keys).
        """
        if keycode <= 0xff:
            specialsnames = {
                ord("\n"): "RETURN",
                ord(" "): "SPACE",
                ord("\t"): "TAB",
                ord("\x7f"): "DELETE",
                ord("\x08"): "BACKSPACE",
            }
            if keycode in specialsnames:
                return specialsnames[keycode]
            return repr(chr(keycode))
        for name in dir(curses):
            if name.startswith("KEY_") and getattr(curses, name) == keycode:
                return name
        return str(keycode)

    def beep(self, force=False):
        if force or self._dobeep:
            curses.beep()
            # don't beep again (as long as the same key is pressed)
            self._dobeep = False

    def cmd_quit(self):
        self.returnvalue = None
        return True

    def cmd_up(self):
        level = self.levels[-1]
        self.report("up")
        level.moveto(level.curx, level.cury-self.stepy)

    def cmd_down(self):
        level = self.levels[-1]
        self.report("down")
        level.moveto(level.curx, level.cury+self.stepy)

    def cmd_pageup(self):
        level = self.levels[-1]
        self.report("page up")
        level.moveto(level.curx, level.cury-level.mainsizey+self.pageoverlapy)

    def cmd_pagedown(self):
        level = self.levels[-1]
        self.report("page down")
        level.moveto(level.curx, level.cury+level.mainsizey-self.pageoverlapy)

    def cmd_left(self):
        level = self.levels[-1]
        self.report("left")
        level.moveto(level.curx-self.stepx, level.cury)

    def cmd_right(self):
        level = self.levels[-1]
        self.report("right")
        level.moveto(level.curx+self.stepx, level.cury)

    def cmd_home(self):
        level = self.levels[-1]
        self.report("home")
        level.moveto(0, level.cury)

    def cmd_end(self):
        level = self.levels[-1]
        self.report("end")
        level.moveto(level.datasizex+level.mainsizey-self.pageoverlapx, level.cury)

    def cmd_prevattr(self):
        level = self.levels[-1]
        if level.displayattr[0] is None or level.displayattr[0] == 0:
            self.beep()
        else:
            self.report("prevattr")
            pos = 0
            for (i, attrname) in enumerate(level.displayattrs):
                if i == level.displayattr[0]-1:
                    break
                pos += level.colwidths[attrname] + 1
            level.moveto(pos, level.cury)

    def cmd_nextattr(self):
        level = self.levels[-1]
        if level.displayattr[0] is None or level.displayattr[0] == len(level.displayattrs)-1:
            self.beep()
        else:
            self.report("nextattr")
            pos = 0
            for (i, attrname) in enumerate(level.displayattrs):
                if i == level.displayattr[0]+1:
                    break
                pos += level.colwidths[attrname] + 1
            level.moveto(pos, level.cury)

    def cmd_pick(self):
        level = self.levels[-1]
        self.returnvalue = level.items[level.cury].item
        return True

    def cmd_pickattr(self):
        level = self.levels[-1]
        attrname = level.displayattr[1]
        if attrname is ipipe.noitem:
            curses.beep()
            self.report(AttributeError(ipipe._attrname(attrname)))
            return
        attr = ipipe._getattr(level.items[level.cury].item, attrname)
        if attr is ipipe.noitem:
            curses.beep()
            self.report(AttributeError(ipipe._attrname(attrname)))
        else:
            self.returnvalue = attr
            return True

    def cmd_pickallattrs(self):
        level = self.levels[-1]
        attrname = level.displayattr[1]
        if attrname is ipipe.noitem:
            curses.beep()
            self.report(AttributeError(ipipe._attrname(attrname)))
            return
        result = []
        for cache in level.items:
            attr = ipipe._getattr(cache.item, attrname)
            if attr is not ipipe.noitem:
                result.append(attr)
        self.returnvalue = result
        return True

    def cmd_pickmarked(self):
        level = self.levels[-1]
        self.returnvalue = [cache.item for cache in level.items if cache.marked]
        return True

    def cmd_pickmarkedattr(self):
        level = self.levels[-1]
        attrname = level.displayattr[1]
        if attrname is ipipe.noitem:
            curses.beep()
            self.report(AttributeError(ipipe._attrname(attrname)))
            return
        result = []
        for cache in level.items:
            if cache.marked:
                attr = ipipe._getattr(cache.item, attrname)
                if attr is not ipipe.noitem:
                    result.append(attr)
        self.returnvalue = result
        return True

    def cmd_markrange(self):
        level = self.levels[-1]
        self.report("markrange")
        start = None
        if level.items:
            for i in xrange(level.cury, -1, -1):
                if level.items[i].marked:
                    start = i
                    break
        if start is None:
            self.report(CommandError("no mark before cursor"))
            curses.beep()
        else:
            for i in xrange(start, level.cury+1):
                cache = level.items[i]
                if not cache.marked:
                    cache.marked = True
                    level.marked += 1

    def cmd_enterdefault(self):
        level = self.levels[-1]
        try:
            item = level.items[level.cury].item
        except IndexError:
            self.report(CommandError("No object"))
            curses.beep()
        else:
            self.report("entering object (default mode)...")
            self.enter(item, "default")

    def cmd_leave(self):
        self.report("leave")
        if len(self.levels) > 1:
            self._calcheaderlines(len(self.levels)-1)
            self.levels.pop(-1)
        else:
            self.report(CommandError("This is the last level"))
            curses.beep()

    def cmd_enter(self):
        level = self.levels[-1]
        try:
            item = level.items[level.cury].item
        except IndexError:
            self.report(CommandError("No object"))
            curses.beep()
        else:
            self.report("entering object...")
            self.enter(item, None)

    def cmd_enterattr(self):
        level = self.levels[-1]
        attrname = level.displayattr[1]
        if attrname is ipipe.noitem:
            curses.beep()
            self.report(AttributeError(ipipe._attrname(attrname)))
            return
        try:
            item = level.items[level.cury].item
        except IndexError:
            self.report(CommandError("No object"))
            curses.beep()
        else:
            attr = ipipe._getattr(item, attrname)
            if attr is ipipe.noitem:
                self.report(AttributeError(ipipe._attrname(attrname)))
            else:
                self.report("entering object attribute %s..." % ipipe._attrname(attrname))
                self.enter(attr, None)

    def cmd_detail(self):
        level = self.levels[-1]
        try:
            item = level.items[level.cury].item
        except IndexError:
            self.report(CommandError("No object"))
            curses.beep()
        else:
            self.report("entering detail view for object...")
            self.enter(item, "detail")

    def cmd_detailattr(self):
        level = self.levels[-1]
        attrname = level.displayattr[1]
        if attrname is ipipe.noitem:
            curses.beep()
            self.report(AttributeError(ipipe._attrname(attrname)))
            return
        try:
            item = level.items[level.cury].item
        except IndexError:
            self.report(CommandError("No object"))
            curses.beep()
        else:
            attr = ipipe._getattr(item, attrname)
            if attr is ipipe.noitem:
                self.report(AttributeError(ipipe._attrname(attrname)))
            else:
                self.report("entering detail view for attribute...")
                self.enter(attr, "detail")

    def cmd_tooglemark(self):
        level = self.levels[-1]
        self.report("toggle mark")
        try:
            item = level.items[level.cury]
        except IndexError: # no items?
            pass
        else:
            if item.marked:
                item.marked = False
                level.marked -= 1
            else:
                item.marked = True
                level.marked += 1

    def cmd_sortattrasc(self):
        level = self.levels[-1]
        attrname = level.displayattr[1]
        if attrname is ipipe.noitem:
            curses.beep()
            self.report(AttributeError(ipipe._attrname(attrname)))
            return
        self.report("sort by %s (ascending)" % ipipe._attrname(attrname))
        def key(item):
            try:
                return ipipe._getattr(item, attrname, None)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                return None
        level.sort(key)

    def cmd_sortattrdesc(self):
        level = self.levels[-1]
        attrname = level.displayattr[1]
        if attrname is ipipe.noitem:
            curses.beep()
            self.report(AttributeError(ipipe._attrname(attrname)))
            return
        self.report("sort by %s (descending)" % ipipe._attrname(attrname))
        def key(item):
            try:
                return ipipe._getattr(item, attrname, None)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                return None
        level.sort(key, reverse=True)

    def cmd_goto(self):
        self.startkeyboardinput("goto")

    def cmd_find(self):
        self.startkeyboardinput("find")

    def cmd_findbackwards(self):
        self.startkeyboardinput("findbackwards")

    def cmd_help(self):
        """
        The help command
        """
        for level in self.levels:
            if isinstance(level.input, _BrowserHelp):
                curses.beep()
                self.report(CommandError("help already active"))
                return

        self.enter(_BrowserHelp(self), "default")

    def _dodisplay(self, scr):
        """
        This method is the workhorse of the browser. It handles screen
        drawing and the keyboard.
        """
        self.scr = scr
        curses.halfdelay(1)
        footery = 2

        keys = []
        for (key, cmd) in self.keymap.iteritems():
            if cmd == "quit":
                keys.append("%s=%s" % (self.keylabel(key), cmd))
        for (key, cmd) in self.keymap.iteritems():
            if cmd == "help":
                keys.append("%s=%s" % (self.keylabel(key), cmd))
        helpmsg = " | %s" % " ".join(keys)

        scr.clear()
        msg = "Fetching first batch of objects..."
        (self.scrsizey, self.scrsizex) = scr.getmaxyx()
        scr.addstr(self.scrsizey//2, (self.scrsizex-len(msg))//2, msg)
        scr.refresh()

        lastc = -1

        self.levels = []
        # enter the first level
        self.enter(self.input, ipipe.xiter(self.input, "default"), *self.attrs)

        self._calcheaderlines(None)

        while True:
            level = self.levels[-1]
            (self.scrsizey, self.scrsizex) = scr.getmaxyx()
            level.mainsizey = self.scrsizey-1-self._headerlines-footery

            # Paint object header
            for i in xrange(self._firstheaderline, self._firstheaderline+self._headerlines):
                lv = self.levels[i]
                posx = 0
                posy = i-self._firstheaderline
                endx = self.scrsizex
                if i: # not the first level
                    msg = " (%d/%d" % (self.levels[i-1].cury, len(self.levels[i-1].items))
                    if not self.levels[i-1].exhausted:
                        msg += "+"
                    msg += ") "
                    endx -= len(msg)+1
                posx += self.addstr(posy, posx, 0, endx, " ibrowse #%d: " % i, self.style_objheadertext)
                for (style, text) in lv.header:
                    posx += self.addstr(posy, posx, 0, endx, text, self.style_objheaderobject)
                    if posx >= endx:
                        break
                if i:
                    posx += self.addstr(posy, posx, 0, self.scrsizex, msg, self.style_objheadernumber)
                posx += self.addchr(posy, posx, 0, self.scrsizex, " ", self.scrsizex-posx, self.style_objheadernumber)

            if not level.items:
                self.addchr(self._headerlines, 0, 0, self.scrsizex, " ", self.scrsizex, self.style_colheader)
                self.addstr(self._headerlines+1, 0, 0, self.scrsizex, " <empty>", astyle.style_error)
                scr.clrtobot()
            else:
                # Paint column headers
                scr.move(self._headerlines, 0)
                scr.addstr(" %*s " % (level.numbersizex, "#"), self.getstyle(self.style_colheader))
                scr.addstr(self.headersepchar, self.getstyle(self.style_colheadersep))
                begx = level.numbersizex+3
                posx = begx-level.datastartx
                for attrname in level.displayattrs:
                    strattrname = ipipe._attrname(attrname)
                    cwidth = level.colwidths[attrname]
                    header = strattrname.ljust(cwidth)
                    if attrname == level.displayattr[1]:
                        style = self.style_colheaderhere
                    else:
                        style = self.style_colheader
                    posx += self.addstr(self._headerlines, posx, begx, self.scrsizex, header, style)
                    posx += self.addstr(self._headerlines, posx, begx, self.scrsizex, self.headersepchar, self.style_colheadersep)
                    if posx >= self.scrsizex:
                        break
                else:
                    scr.addstr(" "*(self.scrsizex-posx), self.getstyle(self.style_colheader))

                # Paint rows
                posy = self._headerlines+1+level.datastarty
                for i in xrange(level.datastarty, min(level.datastarty+level.mainsizey, len(level.items))):
                    cache = level.items[i]
                    if i == level.cury:
                        style = self.style_numberhere
                    else:
                        style = self.style_number

                    posy = self._headerlines+1+i-level.datastarty
                    posx = begx-level.datastartx

                    scr.move(posy, 0)
                    scr.addstr(" %*d%s" % (level.numbersizex, i, " !"[cache.marked]), self.getstyle(style))
                    scr.addstr(self.headersepchar, self.getstyle(self.style_sep))

                    for attrname in level.displayattrs:
                        cwidth = level.colwidths[attrname]
                        try:
                            (align, length, parts) = level.displayrows[i-level.datastarty][attrname]
                        except KeyError:
                            align = 2
                            style = astyle.style_nodata
                        padstyle = self.style_datapad
                        sepstyle = self.style_sep
                        if i == level.cury:
                            padstyle = self.getstylehere(padstyle)
                            sepstyle = self.getstylehere(sepstyle)
                        if align == 2:
                            posx += self.addchr(posy, posx, begx, self.scrsizex, self.nodatachar, cwidth, style)
                        else:
                            if align == 1:
                                posx += self.addchr(posy, posx, begx, self.scrsizex, self.datapadchar, cwidth-length, padstyle)
                            elif align == 0:
                                pad1 = (cwidth-length)//2
                                pad2 = cwidth-length-len(pad1)
                                posx += self.addchr(posy, posx, begx, self.scrsizex, self.datapadchar, pad1, padstyle)
                            for (style, text) in parts:
                                if i == level.cury:
                                    style = self.getstylehere(style)
                                posx += self.addstr(posy, posx, begx, self.scrsizex, text, style)
                                if posx >= self.scrsizex:
                                    break
                            if align == -1:
                                posx += self.addchr(posy, posx, begx, self.scrsizex, self.datapadchar, cwidth-length, padstyle)
                            elif align == 0:
                                posx += self.addchr(posy, posx, begx, self.scrsizex, self.datapadchar, pad2, padstyle)
                        posx += self.addstr(posy, posx, begx, self.scrsizex, self.datasepchar, sepstyle)
                    else:
                        scr.clrtoeol()

                # Add blank row headers for the rest of the screen
                for posy in xrange(posy+1, self.scrsizey-2):
                    scr.addstr(posy, 0, " " * (level.numbersizex+2), self.getstyle(self.style_colheader))
                    scr.clrtoeol()

            posy = self.scrsizey-footery
            # Display footer
            scr.addstr(posy, 0, " "*self.scrsizex, self.getstyle(self.style_footer))

            if level.exhausted:
                flag = ""
            else:
                flag = "+"

            endx = self.scrsizex-len(helpmsg)-1
            scr.addstr(posy, endx, helpmsg, self.getstyle(self.style_footer))

            posx = 0
            msg = " %d%s objects (%d marked): " % (len(level.items), flag, level.marked)
            posx += self.addstr(posy, posx, 0, endx, msg, self.style_footer)
            try:
                item = level.items[level.cury].item
            except IndexError: # empty
                pass
            else:
                for (nostyle, text) in ipipe.xrepr(item, "footer"):
                    if not isinstance(nostyle, int):
                        posx += self.addstr(posy, posx, 0, endx, text, self.style_footer)
                        if posx >= endx:
                            break

                attrstyle = [(astyle.style_default, "no attribute")]
                attrname = level.displayattr[1]
                if attrname is not ipipe.noitem and attrname is not None:
                    posx += self.addstr(posy, posx, 0, endx, " | ", self.style_footer)
                    posx += self.addstr(posy, posx, 0, endx, ipipe._attrname(attrname), self.style_footer)
                    posx += self.addstr(posy, posx, 0, endx, ": ", self.style_footer)
                    try:
                        attr = ipipe._getattr(item, attrname)
                    except (SystemExit, KeyboardInterrupt):
                        raise
                    except Exception, exc:
                        attr = exc
                    if attr is not ipipe.noitem:
                        attrstyle = ipipe.xrepr(attr, "footer")
                    for (nostyle, text) in attrstyle:
                        if not isinstance(nostyle, int):
                            posx += self.addstr(posy, posx, 0, endx, text, self.style_footer)
                            if posx >= endx:
                                break

            try:
                # Display input prompt
                if self.mode in self.prompts:
                    history = self.prompts[self.mode]
                    posx = 0
                    posy = self.scrsizey-1
                    posx += self.addstr(posy, posx, 0, endx, history.prompt, astyle.style_default)
                    posx += self.addstr(posy, posx, 0, endx, " [", astyle.style_default)
                    if history.cury==-1:
                        text = "new"
                    else:
                        text = str(history.cury+1)
                    posx += self.addstr(posy, posx, 0, endx, text, astyle.style_type_number)
                    if history.history:
                        posx += self.addstr(posy, posx, 0, endx, "/", astyle.style_default)
                        posx += self.addstr(posy, posx, 0, endx, str(len(history.history)), astyle.style_type_number)
                    posx += self.addstr(posy, posx, 0, endx, "]: ", astyle.style_default)
                    inputstartx = posx
                    posx += self.addstr(posy, posx, 0, endx, history.input, astyle.style_default)
                # Display report
                else:
                    if self._report is not None:
                        if isinstance(self._report, Exception):
                            style = self.getstyle(astyle.style_error)
                            if self._report.__class__.__module__ == "exceptions":
                                msg = "%s: %s" % \
                                      (self._report.__class__.__name__, self._report)
                            else:
                                msg = "%s.%s: %s" % \
                                      (self._report.__class__.__module__,
                                       self._report.__class__.__name__, self._report)
                        else:
                            style = self.getstyle(self.style_report)
                            msg = self._report
                        scr.addstr(self.scrsizey-1, 0, msg[:self.scrsizex], style)
                        self._report = None
                    else:
                        scr.move(self.scrsizey-1, 0)
            except curses.error:
                # Protect against errors from writing to the last line
                pass
            scr.clrtoeol()

            # Position cursor
            if self.mode in self.prompts:
                history = self.prompts[self.mode]
                scr.move(self.scrsizey-1, inputstartx+history.curx)
            else:
                scr.move(
                    1+self._headerlines+level.cury-level.datastarty,
                    level.numbersizex+3+level.curx-level.datastartx
                )
            scr.refresh()

            # Check keyboard
            while True:
                c = scr.getch()
                if self.mode in self.prompts:
                    if self.prompts[self.mode].handlekey(self, c):
                       break # Redisplay
                else:
                    # if no key is pressed slow down and beep again
                    if c == -1:
                        self.stepx = 1.
                        self.stepy = 1.
                        self._dobeep = True
                    else:
                        # if a different key was pressed slow down and beep too
                        if c != lastc:
                            lastc = c
                            self.stepx = 1.
                            self.stepy = 1.
                            self._dobeep = True
                        cmdname = self.keymap.get(c, None)
                        if cmdname is None:
                            self.report(
                                UnassignedKeyError("Unassigned key %s" %
                                                   self.keylabel(c)))
                        else:
                            cmdfunc = getattr(self, "cmd_%s" % cmdname, None)
                            if cmdfunc is None:
                                self.report(
                                    UnknownCommandError("Unknown command %r" %
                                                        (cmdname,)))
                            elif cmdfunc():
                                returnvalue = self.returnvalue
                                self.returnvalue = None
                                return returnvalue
                        self.stepx = self.nextstepx(self.stepx)
                        self.stepy = self.nextstepy(self.stepy)
                        curses.flushinp() # get rid of type ahead
                        break # Redisplay
        self.scr = None

    def display(self):
        return curses.wrapper(self._dodisplay)
