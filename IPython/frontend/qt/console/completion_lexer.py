# System library imports
from pygments.token import Token, is_token_subtype


class CompletionLexer(object):
    """ Uses Pygments and some auxillary information to lex code snippets for 
        symbol contexts.
    """

    # Maps Lexer names to a list of possible name separators
    separator_map = { 'C' : [ '.', '->' ],
                      'C++' : [ '.', '->', '::' ],
                      'Python' : [ '.' ] }

    def __init__(self, lexer):
        self.lexer = lexer

    def get_context(self, string):
        """ Assuming the cursor is at the end of the specified string, get the
            context (a list of names) for the symbol at cursor position.
        """
        context = []
        reversed_tokens = list(self._lexer.get_tokens(string))
        reversed_tokens.reverse()

        # Pygments often tacks on a newline when none is specified in the input
        if reversed_tokens and reversed_tokens[0][1].endswith('\n') and \
                not string.endswith('\n'):
            reversed_tokens.pop(0)

        current_op = unicode()
        for token, text in reversed_tokens:
            if is_token_subtype(token, Token.Name) and \
                    (not context or current_op in self._name_separators):
                if not context and current_op in self._name_separators:
                    context.insert(0, unicode())
                context.insert(0, text)
                current_op = unicode()
            elif token is Token.Operator or token is Token.Punctuation:
                current_op = text + current_op
            else:
                break

        return context

    def get_lexer(self, lexer):
        return self._lexer

    def set_lexer(self, lexer, name_separators=None):
        self._lexer = lexer
        if name_separators is None:
            self._name_separators = self.separator_map.get(lexer.name, ['.'])
        else:
            self._name_separators = list(name_separators)

    lexer = property(get_lexer, set_lexer)
    
