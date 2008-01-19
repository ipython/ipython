# -*- coding: iso-8859-1 -*-

import curses, fcntl, signal, struct, tty, textwrap, inspect

from IPython import ipapi

import astyle, ipipe


# Python 2.3 compatibility
try:
    set
except NameError:
    import sets
    set = sets.Set

# Python 2.3 compatibility
try:
    sorted
except NameError:
    from ipipe import sorted


class UnassignedKeyError(Exception):
    """
    Exception that is used for reporting unassigned keys.
    """


class UnknownCommandError(Exception):
    """
    Exception that is used for reporting unknown commands (this should never
    happen).
    """


class CommandError(Exception):
    """
    Exception that is used for reporting that a command can't be executed.
    """


class Keymap(dict):
    """
    Stores mapping of keys to commands.
    """
    def __init__(self):
        self._keymap = {}

    def __setitem__(self, key, command):
        if isinstance(key, str):
            for c in key:
                dict.__setitem__(self, ord(c), command)
        else:
            dict.__setitem__(self, key, command)

    def __getitem__(self, key):
        if isinstance(key, str):
            key = ord(key)
        return dict.__getitem__(self, key)

    def __detitem__(self, key):
        if isinstance(key, str):
            key = ord(key)
        dict.__detitem__(self, key)

    def register(self, command, *keys):
        for key in keys:
            self[key] = command

    def get(self, key, default=None):
        if isinstance(key, str):
            key = ord(key)
        return dict.get(self, key, default)

    def findkey(self, command, default=ipipe.noitem):
        for (key, commandcandidate) in self.iteritems():
            if commandcandidate == command:
                return key
        if default is ipipe.noitem:
            raise KeyError(command)
        return default


class _BrowserCachedItem(object):
    # This is used internally by ``ibrowse`` to store a item together with its
    # marked status.
    __slots__ = ("item", "marked")

    def __init__(self, item):
        self.item = item
        self.marked = False


class _BrowserHelp(object):
    style_header = astyle.Style.fromstr("yellow:black:bold")
    # This is used internally by ``ibrowse`` for displaying the help screen.
    def __init__(self, browser):
        self.browser = browser

    def __xrepr__(self, mode):
        yield (-1, True)
        if mode == "header" or mode == "footer":
            yield (astyle.style_default, "ibrowse help screen")
        else:
            yield (astyle.style_default, repr(self))

    def __iter__(self):
        # Get reverse key mapping
        allkeys = {}
        for (key, cmd) in self.browser.keymap.iteritems():
            allkeys.setdefault(cmd, []).append(key)

        fields = ("key", "description")

        commands = []
        for name in dir(self.browser):
            if name.startswith("cmd_"):
                command = getattr(self.browser, name)
                commands.append((inspect.getsourcelines(command)[-1], name[4:], command))
        commands.sort()
        commands = [(c[1], c[2]) for c in commands]
        for (i, (name, command)) in enumerate(commands):
            if i:
                yield ipipe.Fields(fields, key="", description="")

            description = command.__doc__
            if description is None:
                lines = []
            else:
                lines = [l.strip() for l in description.splitlines() if l.strip()]
                description = "\n".join(lines)
                lines = textwrap.wrap(description, 60)
            keys = allkeys.get(name, [])

            yield ipipe.Fields(fields, key="", description=astyle.Text((self.style_header, name)))
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
    def __init__(self, browser, input, mainsizey, *attrs):
        self.browser = browser
        self.input = input
        self.header = [x for x in ipipe.xrepr(input, "header") if not isinstance(x[0], int)]
        # iterator for the input
        self.iterator = ipipe.xiter(input)

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

        # Attributes to display (in this order)
        self.displayattrs = []

        # index and attribute under the cursor
        self.displayattr = (None, ipipe.noitem)

        # Maps attributes to column widths
        self.colwidths = {}

        # Set of hidden attributes
        self.hiddenattrs = set()

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
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception, exc:
                have += 1
                self.items.append(_BrowserCachedItem(exc))
                self.exhausted = True
                break
            else:
                have += 1
                self.items.append(_BrowserCachedItem(item))

    def calcdisplayattrs(self):
        # Calculate which attributes are available from the objects that are
        # currently visible on screen (and store it in ``self.displayattrs``)

        attrs = set()
        self.displayattrs = []
        if self.attrs:
            # If the browser object specifies a fixed list of attributes,
            # simply use it (removing hidden attributes).
            for attr in self.attrs:
                attr = ipipe.upgradexattr(attr)
                if attr not in attrs and attr not in self.hiddenattrs:
                    self.displayattrs.append(attr)
                    attrs.add(attr)
        else:
            endy = min(self.datastarty+self.mainsizey, len(self.items))
            for i in xrange(self.datastarty, endy):
                for attr in ipipe.xattrs(self.items[i].item, "default"):
                    if attr not in attrs and attr not in self.hiddenattrs:
                        self.displayattrs.append(attr)
                        attrs.add(attr)

    def getrow(self, i):
        # Return a dictionary with the attributes for the object
        # ``self.items[i]``. Attribute names are taken from
        # ``self.displayattrs`` so ``calcdisplayattrs()`` must have been
        # called before.
        row = {}
        item = self.items[i].item
        for attr in self.displayattrs:
            try:
                value = attr.value(item)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception, exc:
                value = exc
            # only store attribute if it exists (or we got an exception)
            if value is not ipipe.noitem:
                # remember alignment, length and colored text
                row[attr] = ipipe.xformat(value, "cell", self.browser.maxattrlength)
        return row

    def calcwidths(self):
        # Recalculate the displayed fields and their widths.
        # ``calcdisplayattrs()'' must have been called and the cache
        # for attributes of the objects on screen (``self.displayrows``)
        # must have been filled. This sets ``self.colwidths`` which maps
        # attribute descriptors to widths.
        self.colwidths = {}
        for row in self.displayrows:
            for attr in self.displayattrs:
                try:
                    length = row[attr][1]
                except KeyError:
                    length = 0
                # always add attribute to colwidths, even if it doesn't exist
                if attr not in self.colwidths:
                    self.colwidths[attr] = len(attr.name())
                newwidth = max(self.colwidths[attr], length)
                self.colwidths[attr] = newwidth

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
        for (i, attr) in enumerate(self.displayattrs):
            if pos+self.colwidths[attr] >= self.curx:
                self.displayattr = (i, attr)
                break
            pos += self.colwidths[attr]+1
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
                for i in xrange(min(olddatastarty, self.datastarty+self.mainsizey)-1,
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
                for i in xrange(max(olddatastarty+self.mainsizey, self.datastarty),
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

    def refresh(self):
        """
        Restart iterating the input.
        """
        self.iterator = ipipe.xiter(self.input)
        self.items.clear()
        self.exhausted = False
        self.datastartx = self.datastarty = 0
        self.moveto(0, 0, refresh=True)

    def refreshfind(self):
        """
        Restart iterating the input and go back to the same object as before
        (if it can be found in the new iterator).
        """
        try:
            oldobject = self.items[self.cury].item
        except IndexError:
            oldobject = ipipe.noitem
        self.iterator = ipipe.xiter(self.input)
        self.items.clear()
        self.exhausted = False
        while True:
            self.fetch(len(self.items)+1)
            if self.exhausted:
                curses.beep()
                self.datastartx = self.datastarty = 0
                self.moveto(self.curx, 0, refresh=True)
                break
            if self.items[-1].item == oldobject:
                self.datastartx = self.datastarty = 0
                self.moveto(self.curx, len(self.items)-1, refresh=True)
                break


class _CommandInput(object):
    keymap = Keymap()
    keymap.register("left", curses.KEY_LEFT)
    keymap.register("right", curses.KEY_RIGHT)
    keymap.register("home", curses.KEY_HOME, "\x01") # Ctrl-A
    keymap.register("end", curses.KEY_END, "\x05") # Ctrl-E
    # FIXME: What's happening here?
    keymap.register("backspace", curses.KEY_BACKSPACE, "\x08\x7f")
    keymap.register("delete", curses.KEY_DC)
    keymap.register("delend", 0x0b) # Ctrl-K
    keymap.register("execute", "\r\n")
    keymap.register("up", curses.KEY_UP)
    keymap.register("down", curses.KEY_DOWN)
    keymap.register("incsearchup", curses.KEY_PPAGE)
    keymap.register("incsearchdown", curses.KEY_NPAGE)
    keymap.register("exit", "\x18"), # Ctrl-X

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

    def cmd_delend(self, browser):
        if self.curx<len(self.input):
            self.input = self.input[:self.curx]
            return True

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

    def cmd_incsearchup(self, browser):
        prefix = self.input[:self.curx]
        cury = self.cury
        while True:
            cury += 1
            if cury >= len(self.history):
                break
            if self.history[cury].startswith(prefix):
                self.input = self.history[cury]
                self.cury = cury
                return True
        curses.beep()

    def cmd_incsearchdown(self, browser):
        prefix = self.input[:self.curx]
        cury = self.cury
        while True:
            cury -= 1
            if cury <= 0:
                break
            if self.history[cury].startswith(prefix):
                self.input = self.history[self.cury]
                self.cury = cury
                return True
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
    keymap = Keymap()
    keymap.register("quit", "q")
    keymap.register("up", curses.KEY_UP)
    keymap.register("down", curses.KEY_DOWN)
    keymap.register("pageup", curses.KEY_PPAGE)
    keymap.register("pagedown", curses.KEY_NPAGE)
    keymap.register("left", curses.KEY_LEFT)
    keymap.register("right", curses.KEY_RIGHT)
    keymap.register("home", curses.KEY_HOME, "\x01")
    keymap.register("end", curses.KEY_END, "\x05")
    keymap.register("prevattr", "<\x1b")
    keymap.register("nextattr", ">\t")
    keymap.register("pick", "p")
    keymap.register("pickattr", "P")
    keymap.register("pickallattrs", "C")
    keymap.register("pickmarked", "m")
    keymap.register("pickmarkedattr", "M")
    keymap.register("pickinput", "i")
    keymap.register("pickinputattr", "I")
    keymap.register("hideattr", "h")
    keymap.register("unhideattrs", "H")
    keymap.register("help", "?")
    keymap.register("enter", "\r\n")
    keymap.register("enterattr", "E")
    # FIXME: What's happening here?
    keymap.register("leave", curses.KEY_BACKSPACE, "x\x08\x7f")
    keymap.register("detail", "d")
    keymap.register("detailattr", "D")
    keymap.register("tooglemark", " ")
    keymap.register("markrange", "%")
    keymap.register("sortattrasc", "v")
    keymap.register("sortattrdesc", "V")
    keymap.register("goto", "g")
    keymap.register("find", "f")
    keymap.register("findbackwards", "b")
    keymap.register("refresh", "r")
    keymap.register("refreshfind", "R")

    def __init__(self, input=None, *attrs):
        """
        Create a new browser. If ``attrs`` is not empty, it is the list
        of attributes that will be displayed in the browser, otherwise
        these will be determined by the objects on screen.
        """
        ipipe.Display.__init__(self, input)

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

        # set by the SIGWINCH signal handler
        self.resized = False

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
        return astyle.Style(style.fg, astyle.COLOR_BLUE, style.attrs | astyle.A_BOLD)

    def report(self, msg):
        """
        Store the message ``msg`` for display below the footer line. This
        will be displayed as soon as the screen is redrawn.
        """
        self._report = msg

    def enter(self, item, *attrs):
        """
        Enter the object ``item``. If ``attrs`` is specified, it will be used
        as a fixed list of attributes to display.
        """
        if self.levels and item is self.levels[-1].input:
            curses.beep()
            self.report(CommandError("Recursion on input object"))
        else:
            oldlevels = len(self.levels)
            self._calcheaderlines(oldlevels+1)
            try:
                level = _BrowserLevel(
                    self,
                    item,
                    self.scrsizey-1-self._headerlines-2,
                    *attrs
                )
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception, exc:
                if not self.levels:
                    raise
                self._calcheaderlines(oldlevels)
                curses.beep()
                self.report(exc)
            else:
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
            elif 0x00 < keycode < 0x20:
                return "CTRL-%s" % chr(keycode + 64)
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

    def cmd_up(self):
        """
        Move the cursor to the previous row.
        """
        level = self.levels[-1]
        self.report("up")
        level.moveto(level.curx, level.cury-self.stepy)

    def cmd_down(self):
        """
        Move the cursor to the next row.
        """
        level = self.levels[-1]
        self.report("down")
        level.moveto(level.curx, level.cury+self.stepy)

    def cmd_pageup(self):
        """
        Move the cursor up one page.
        """
        level = self.levels[-1]
        self.report("page up")
        level.moveto(level.curx, level.cury-level.mainsizey+self.pageoverlapy)

    def cmd_pagedown(self):
        """
        Move the cursor down one page.
        """
        level = self.levels[-1]
        self.report("page down")
        level.moveto(level.curx, level.cury+level.mainsizey-self.pageoverlapy)

    def cmd_left(self):
        """
        Move the cursor left.
        """
        level = self.levels[-1]
        self.report("left")
        level.moveto(level.curx-self.stepx, level.cury)

    def cmd_right(self):
        """
        Move the cursor right.
        """
        level = self.levels[-1]
        self.report("right")
        level.moveto(level.curx+self.stepx, level.cury)

    def cmd_home(self):
        """
        Move the cursor to the first column.
        """
        level = self.levels[-1]
        self.report("home")
        level.moveto(0, level.cury)

    def cmd_end(self):
        """
        Move the cursor to the last column.
        """
        level = self.levels[-1]
        self.report("end")
        level.moveto(level.datasizex+level.mainsizey-self.pageoverlapx, level.cury)

    def cmd_prevattr(self):
        """
        Move the cursor one attribute column to the left.
        """
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
        """
        Move the cursor one attribute column to the right.
        """
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
        """
        'Pick' the object under the cursor (i.e. the row the cursor is on).
        This leaves the browser and returns the picked object to the caller.
        (In IPython this object will be available as the ``_`` variable.)
        """
        level = self.levels[-1]
        self.returnvalue = level.items[level.cury].item
        return True

    def cmd_pickattr(self):
        """
        'Pick' the attribute under the cursor (i.e. the row/column the
        cursor is on).
        """
        level = self.levels[-1]
        attr = level.displayattr[1]
        if attr is ipipe.noitem:
            curses.beep()
            self.report(CommandError("no column under cursor"))
            return
        value = attr.value(level.items[level.cury].item)
        if value is ipipe.noitem:
            curses.beep()
            self.report(AttributeError(attr.name()))
        else:
            self.returnvalue = value
            return True

    def cmd_pickallattrs(self):
        """
        Pick' the complete column under the cursor (i.e. the attribute under
        the cursor) from all currently fetched objects. These attributes
        will be returned as a list.
        """
        level = self.levels[-1]
        attr = level.displayattr[1]
        if attr is ipipe.noitem:
            curses.beep()
            self.report(CommandError("no column under cursor"))
            return
        result = []
        for cache in level.items:
            value = attr.value(cache.item)
            if value is not ipipe.noitem:
                result.append(value)
        self.returnvalue = result
        return True

    def cmd_pickmarked(self):
        """
        'Pick' marked objects. Marked objects will be returned as a list.
        """
        level = self.levels[-1]
        self.returnvalue = [cache.item for cache in level.items if cache.marked]
        return True

    def cmd_pickmarkedattr(self):
        """
        'Pick' the attribute under the cursor from all marked objects
        (This returns a list).
        """

        level = self.levels[-1]
        attr = level.displayattr[1]
        if attr is ipipe.noitem:
            curses.beep()
            self.report(CommandError("no column under cursor"))
            return
        result = []
        for cache in level.items:
            if cache.marked:
                value = attr.value(cache.item)
                if value is not ipipe.noitem:
                    result.append(value)
        self.returnvalue = result
        return True

    def cmd_pickinput(self):
        """
        Use the object under the cursor (i.e. the row the cursor is on) as
        the next input line. This leaves the browser and puts the picked object
        in the input.
        """
        level = self.levels[-1]
        value = level.items[level.cury].item
        self.returnvalue = None
        api = ipapi.get()
        api.set_next_input(str(value))
        return True

    def cmd_pickinputattr(self):
        """
        Use the attribute under the cursor i.e. the row/column the cursor is on)
        as the next input line. This leaves the browser and puts the picked
        object in the input.
        """
        level = self.levels[-1]
        attr = level.displayattr[1]
        if attr is ipipe.noitem:
            curses.beep()
            self.report(CommandError("no column under cursor"))
            return
        value = attr.value(level.items[level.cury].item)
        if value is ipipe.noitem:
            curses.beep()
            self.report(AttributeError(attr.name()))
        self.returnvalue = None
        api = ipapi.get()
        api.set_next_input(str(value))
        return True

    def cmd_markrange(self):
        """
        Mark all objects from the last marked object before the current cursor
        position to the cursor position.
        """
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

    def cmd_enter(self):
        """
        Enter the object under the cursor. (what this mean depends on the object
        itself (i.e. how it implements iteration). This opens a new browser 'level'.
        """
        level = self.levels[-1]
        try:
            item = level.items[level.cury].item
        except IndexError:
            self.report(CommandError("No object"))
            curses.beep()
        else:
            self.report("entering object...")
            self.enter(item)

    def cmd_leave(self):
        """
        Leave the current browser level and go back to the previous one.
        """
        self.report("leave")
        if len(self.levels) > 1:
            self._calcheaderlines(len(self.levels)-1)
            self.levels.pop(-1)
        else:
            self.report(CommandError("This is the last level"))
            curses.beep()

    def cmd_enterattr(self):
        """
        Enter the attribute under the cursor.
        """
        level = self.levels[-1]
        attr = level.displayattr[1]
        if attr is ipipe.noitem:
            curses.beep()
            self.report(CommandError("no column under cursor"))
            return
        try:
            item = level.items[level.cury].item
        except IndexError:
            self.report(CommandError("No object"))
            curses.beep()
        else:
            value = attr.value(item)
            name = attr.name()
            if value is ipipe.noitem:
                self.report(AttributeError(name))
            else:
                self.report("entering object attribute %s..." % name)
                self.enter(value)

    def cmd_detail(self):
        """
        Show a detail view of the object under the cursor. This shows the
        name, type, doc string and value of the object attributes (and it
        might show more attributes than in the list view, depending on
        the object).
        """
        level = self.levels[-1]
        try:
            item = level.items[level.cury].item
        except IndexError:
            self.report(CommandError("No object"))
            curses.beep()
        else:
            self.report("entering detail view for object...")
            attrs = [ipipe.AttributeDetail(item, attr) for attr in ipipe.xattrs(item, "detail")]
            self.enter(attrs)

    def cmd_detailattr(self):
        """
        Show a detail view of the attribute under the cursor.
        """
        level = self.levels[-1]
        attr = level.displayattr[1]
        if attr is ipipe.noitem:
            curses.beep()
            self.report(CommandError("no attribute"))
            return
        try:
            item = level.items[level.cury].item
        except IndexError:
            self.report(CommandError("No object"))
            curses.beep()
        else:
            try:
                item = attr.value(item)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception, exc:
                self.report(exc)
            else:
                self.report("entering detail view for attribute %s..." % attr.name())
                attrs = [ipipe.AttributeDetail(item, attr) for attr in ipipe.xattrs(item, "detail")]
                self.enter(attrs)

    def cmd_tooglemark(self):
        """
        Mark/unmark the object under the cursor. Marked objects have a '!'
        after the row number).
        """
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
        """
        Sort the objects (in ascending order) using the attribute under
        the cursor as the sort key.
        """
        level = self.levels[-1]
        attr = level.displayattr[1]
        if attr is ipipe.noitem:
            curses.beep()
            self.report(CommandError("no column under cursor"))
            return
        self.report("sort by %s (ascending)" % attr.name())
        def key(item):
            try:
                return attr.value(item)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                return None
        level.sort(key)

    def cmd_sortattrdesc(self):
        """
        Sort the objects (in descending order) using the attribute under
        the cursor as the sort key.
        """
        level = self.levels[-1]
        attr = level.displayattr[1]
        if attr is ipipe.noitem:
            curses.beep()
            self.report(CommandError("no column under cursor"))
            return
        self.report("sort by %s (descending)" % attr.name())
        def key(item):
            try:
                return attr.value(item)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                return None
        level.sort(key, reverse=True)

    def cmd_hideattr(self):
        """
        Hide the attribute under the cursor.
        """
        level = self.levels[-1]
        if level.displayattr[0] is None:
            self.beep()
        else:
            self.report("hideattr")
            level.hiddenattrs.add(level.displayattr[1])
            level.moveto(level.curx, level.cury, refresh=True)

    def cmd_unhideattrs(self):
        """
        Make all attributes visible again.
        """
        level = self.levels[-1]
        self.report("unhideattrs")
        level.hiddenattrs.clear()
        level.moveto(level.curx, level.cury, refresh=True)

    def cmd_goto(self):
        """
        Jump to a row. The row number can be entered at the
        bottom of the screen.
        """
        self.startkeyboardinput("goto")

    def cmd_find(self):
        """
        Search forward for a row. The search condition can be entered at the
        bottom of the screen.
        """
        self.startkeyboardinput("find")

    def cmd_findbackwards(self):
        """
        Search backward for a row. The search condition can be entered at the
        bottom of the screen.
        """
        self.startkeyboardinput("findbackwards")

    def cmd_refresh(self):
        """
        Refreshes the display by restarting the iterator.
        """
        level = self.levels[-1]
        self.report("refresh")
        level.refresh()

    def cmd_refreshfind(self):
        """
        Refreshes the display by restarting the iterator and goes back to the
        same object the cursor was on before restarting (if this object can't be
        found the cursor jumps back to the first object).
        """
        level = self.levels[-1]
        self.report("refreshfind")
        level.refreshfind()

    def cmd_help(self):
        """
        Opens the help screen as a new browser level, describing keyboard
        shortcuts.
        """
        for level in self.levels:
            if isinstance(level.input, _BrowserHelp):
                curses.beep()
                self.report(CommandError("help already active"))
                return

        self.enter(_BrowserHelp(self))

    def cmd_quit(self):
        """
        Quit the browser and return to the IPython prompt.
        """
        self.returnvalue = None
        return True

    def sigwinchhandler(self, signal, frame):
        self.resized = True

    def _dodisplay(self, scr):
        """
        This method is the workhorse of the browser. It handles screen
        drawing and the keyboard.
        """
        self.scr = scr
        curses.halfdelay(1)
        footery = 2

        keys = []
        for cmd in ("quit", "help"):
            key = self.keymap.findkey(cmd, None)
            if key is not None:
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
        self.enter(self.input, *self.attrs)

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
                for attr in level.displayattrs:
                    attrname = attr.name()
                    cwidth = level.colwidths[attr]
                    header = attrname.ljust(cwidth)
                    if attr is level.displayattr[1]:
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
                            if i == level.cury:
                                style = self.getstylehere(style)
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
                attr = level.displayattr[1]
                if attr is not ipipe.noitem and not isinstance(attr, ipipe.SelfDescriptor):
                    posx += self.addstr(posy, posx, 0, endx, " | ", self.style_footer)
                    posx += self.addstr(posy, posx, 0, endx, attr.name(), self.style_footer)
                    posx += self.addstr(posy, posx, 0, endx, ": ", self.style_footer)
                    try:
                        value = attr.value(item)
                    except (SystemExit, KeyboardInterrupt):
                        raise
                    except Exception, exc:
                        value = exc
                    if value is not ipipe.noitem:
                        attrstyle = ipipe.xrepr(value, "footer")
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
                if self.resized:
                    size = fcntl.ioctl(0, tty.TIOCGWINSZ, "12345678")
                    size = struct.unpack("4H", size)
                    oldsize = scr.getmaxyx()
                    scr.erase()
                    curses.resize_term(size[0], size[1])
                    newsize = scr.getmaxyx()
                    scr.erase()
                    for l in self.levels:
                        l.mainsizey += newsize[0]-oldsize[0]
                        l.moveto(l.curx, l.cury, refresh=True)
                    scr.refresh()
                    self.resized = False
                    break # Redisplay
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
        if hasattr(curses, "resize_term"):
            oldhandler = signal.signal(signal.SIGWINCH, self.sigwinchhandler)
            try:
                return curses.wrapper(self._dodisplay)
            finally:
                signal.signal(signal.SIGWINCH, oldhandler)
        else:
            return curses.wrapper(self._dodisplay)
