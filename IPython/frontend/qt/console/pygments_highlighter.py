# System library imports.
from PyQt4 import QtGui
from pygments.lexer import RegexLexer, _TokenType, Text, Error
from pygments.lexers import PythonLexer
from pygments.styles.default import DefaultStyle
from pygments.token import Comment


def get_tokens_unprocessed(self, text, stack=('root',)):
    """ Split ``text`` into (tokentype, text) pairs.

        Monkeypatched to store the final stack on the object itself.
    """
    pos = 0
    tokendefs = self._tokens
    if hasattr(self, '_saved_state_stack'):
        statestack = list(self._saved_state_stack)
    else:
        statestack = list(stack)
    statetokens = tokendefs[statestack[-1]]
    while 1:
        for rexmatch, action, new_state in statetokens:
            m = rexmatch(text, pos)
            if m:
                if type(action) is _TokenType:
                    yield pos, action, m.group()
                else:
                    for item in action(self, m):
                        yield item
                pos = m.end()
                if new_state is not None:
                    # state transition
                    if isinstance(new_state, tuple):
                        for state in new_state:
                            if state == '#pop':
                                statestack.pop()
                            elif state == '#push':
                                statestack.append(statestack[-1])
                            else:
                                statestack.append(state)
                    elif isinstance(new_state, int):
                        # pop
                        del statestack[new_state:]
                    elif new_state == '#push':
                        statestack.append(statestack[-1])
                    else:
                        assert False, "wrong state def: %r" % new_state
                    statetokens = tokendefs[statestack[-1]]
                break
        else:
            try:
                if text[pos] == '\n':
                    # at EOL, reset state to "root"
                    pos += 1
                    statestack = ['root']
                    statetokens = tokendefs['root']
                    yield pos, Text, u'\n'
                    continue
                yield pos, Error, text[pos]
                pos += 1
            except IndexError:
                break
    self._saved_state_stack = list(statestack)

# Monkeypatch!
RegexLexer.get_tokens_unprocessed = get_tokens_unprocessed


class BlockUserData(QtGui.QTextBlockUserData):
    """ Storage for the user data associated with each line.
    """

    syntax_stack = ('root',)

    def __init__(self, **kwds):
        for key, value in kwds.iteritems():
            setattr(self, key, value)
        QtGui.QTextBlockUserData.__init__(self)

    def __repr__(self):
        attrs = ['syntax_stack']
        kwds = ', '.join([ '%s=%r' % (attr, getattr(self, attr)) 
                           for attr in attrs ])
        return 'BlockUserData(%s)' % kwds


class PygmentsHighlighter(QtGui.QSyntaxHighlighter):
    """ Syntax highlighter that uses Pygments for parsing. """

    def __init__(self, parent, lexer=None):
        super(PygmentsHighlighter, self).__init__(parent)

        self._lexer = lexer if lexer else PythonLexer()
        self._style = DefaultStyle
        # Caches for formats and brushes.
        self._brushes = {}
        self._formats = {}

    def highlightBlock(self, qstring):
        """ Highlight a block of text.
        """
        qstring = unicode(qstring)
        prev_data = self.previous_block_data()

        if prev_data is not None:
            self._lexer._saved_state_stack = prev_data.syntax_stack
        elif hasattr(self._lexer, '_saved_state_stack'):
            del self._lexer._saved_state_stack

        index = 0
        # Lex the text using Pygments
        for token, text in self._lexer.get_tokens(qstring):
            l = len(text)
            format = self._get_format(token)
            if format is not None:
                self.setFormat(index, l, format)
            index += l

        if hasattr(self._lexer, '_saved_state_stack'):
            data = BlockUserData(syntax_stack=self._lexer._saved_state_stack)
            self.currentBlock().setUserData(data)
            # Clean up for the next go-round.
            del self._lexer._saved_state_stack

    def previous_block_data(self):
        """ Convenience method for returning the previous block's user data.
        """
        return self.currentBlock().previous().userData()

    def _get_format(self, token):
        """ Returns a QTextCharFormat for token or None.
        """
        if token in self._formats:
            return self._formats[token]
        result = None
        for key, value in self._style.style_for_token(token).items():
            if value:
                if result is None:
                    result = QtGui.QTextCharFormat()
                if key == 'color':
                    result.setForeground(self._get_brush(value))
                elif key == 'bgcolor':
                    result.setBackground(self._get_brush(value))
                elif key == 'bold':
                    result.setFontWeight(QtGui.QFont.Bold)
                elif key == 'italic':
                    result.setFontItalic(True)
                elif key == 'underline':
                    result.setUnderlineStyle(
                        QtGui.QTextCharFormat.SingleUnderline)
                elif key == 'sans':
                    result.setFontStyleHint(QtGui.QFont.SansSerif)
                elif key == 'roman':
                    result.setFontStyleHint(QtGui.QFont.Times)
                elif key == 'mono':
                    result.setFontStyleHint(QtGui.QFont.TypeWriter)
                elif key == 'border':
                    # Borders are normally used for errors. We can't do a border
                    # so instead we do a wavy underline
                    result.setUnderlineStyle(
                        QtGui.QTextCharFormat.WaveUnderline)
                    result.setUnderlineColor(self._get_color(value))
        self._formats[token] = result
        return result

    def _get_brush(self, color):
        """ Returns a brush for the color.
        """
        result = self._brushes.get(color)
        if result is None:
            qcolor = self._get_color(color)
            result = QtGui.QBrush(qcolor)
            self._brushes[color] = result
        return result

    def _get_color(self, color):
        qcolor = QtGui.QColor()
        qcolor.setRgb(int(color[:2], base=16),
                      int(color[2:4], base=16),
                      int(color[4:6], base=16))
        return qcolor

