# dollarmath.py by Akihiro Uchida *public domain*
# the original one is written by Paul Kienzle
# and published as public domain in [sphinx-dev]: $math$ extension
r"""
Allow $math$ markup in text and docstrings, ignoring \$.

The $math$ markup should be separated from the surrounding text by spaces.
To embed markup within a word, place backslash-space before and after.
For convenience, the final $ can be followed by punctuation
(period, comma or semicolon).
"""

import re

dollar_pat = r"(?:^|(?<=\s))[$]([^\n]*?)(?<![\\])[$](?:$|(?=\s|[.,;\\]))"
_dollar = re.compile(dollar_pat)
_notdollar = re.compile(r"\\[$]")


def replace_dollar(content):
    content = _dollar.sub(r":math:`\1`", content)
    content = _notdollar.sub("$", content)
    return content


def rewrite_rst(app, docname, source):
    source[0] = replace_dollar(source[0])


def rewrite_autodoc(app, what, name, obj, options, lines):
    lines[:] = [replace_dollar(L) for L in lines]


def setup(app):
    app.connect('source-read', rewrite_rst)
    if 'autodoc-process-docstring' in app._events:
        app.connect('autodoc-process-docstring', rewrite_autodoc)


def test_expr(expr, expect):
    result = replace_dollar(expr)
    print 'A math expression: %s' % expr
    print 'A expected output: %s' % expect
    if result == expect:
        print 'OK: A result match expected one'
    else:
        print 'NG: A result %s does not match expected one!' % result


def test_dollar():
    samples = {
        u"no dollar": u"no dollar",
        u"$only$": u":math:`only`",
        u"$first$ is good": u":math:`first` is good",
        u"so is $last$": u"so is :math:`last`",
        u"and $mid$ too": u"and :math:`mid` too",
        u"$first$, $mid$, $last$": u":math:`first`, :math:`mid`, :math:`last`",
        u"dollar\$ escape": u"dollar$ escape",
        u"dollar \$escape\$ too": u"dollar $escape$ too",
        u"emb\ $ed$\ ed": u"emb\ :math:`ed`\ ed",
        u"$first$a": u"$first$a",
        u"a$last$": u"a$last$",
        u"a $mid$dle a": u"a $mid$dle a",
    }
    for expr, expect in samples.items():
        test_expr(expr, expect)


if __name__ == "__main__":
    import sys
    import locale
    import codecs
    encoding = locale.getpreferredencoding()
    sys.stdout = codecs.getwriter(encoding)(sys.stdout)
    sys.stdin = codecs.getreader(encoding)(sys.stdin)

    import optparse
    parser = optparse.OptionParser(usage='usage: %prog [options]')
    parser.add_option("-i", "--input", dest="expr", type="string",
                      help="input $math$ expression to test")
    parser.add_option("-o", "--output", dest="expect", type="string",
                      help="output result you expect")

    opts, args = parser.parse_args()
    if opts.expr:
        expression = unicode(opts.expr, encoding)
        if opts.expect:
            expected = unicode(opts.expect, encoding)
            test_expr(expression, expected)
        else:
            print replace_dollar(expression)
    else:
        if opts.expect:
            parser.print_help()
            parser.error("output option requires input expression")
        else:
            test_dollar()
