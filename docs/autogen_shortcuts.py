from pathlib import Path

from IPython.terminal.shortcuts import create_ipython_shortcuts

def name(c):
    s = c.__class__.__name__
    if s == '_Invert':
        return '(Not: %s)' % name(c.filter)
    if s in log_filters.keys():
        return '(%s: %s)' % (log_filters[s], ', '.join(name(x) for x in c.filters))
    return log_filters[s] if s in log_filters.keys() else s


def sentencize(s):
    """Extract first sentence
    """
    s = s.replace('\n', ' ').strip().split('.')
    s = s[0] if len(s) else s
    try:
        return " ".join(s.split())
    except AttributeError:
        return s


def most_common(lst, n=3):
    """Most common elements occurring more then `n` times
    """
    from collections import Counter

    c = Counter(lst)
    return [k for (k, v) in c.items() if k and v > n]


def multi_filter_str(flt):
    """Yield readable conditional filter
    """
    assert hasattr(flt, 'filters'), 'Conditional filter required'
    yield name(flt)


log_filters = {'_AndList': 'And', '_OrList': 'Or'}
log_invert =  {'_Invert'}

class _DummyTerminal:
    """Used as a buffer to get prompt_toolkit bindings
    """
    handle_return = None
    input_transformer_manager = None
    display_completions = None
    editing_mode = "emacs"


ipy_bindings = create_ipython_shortcuts(_DummyTerminal()).bindings

dummy_docs = []  # ignore bindings without proper documentation

common_docs = most_common([kb.handler.__doc__ for kb in ipy_bindings])
if common_docs:
    dummy_docs.extend(common_docs)

dummy_docs = list(set(dummy_docs))

single_filter = {}
multi_filter =  {}
for kb in ipy_bindings:
    doc = kb.handler.__doc__
    if not doc or doc in dummy_docs:
        continue

    shortcut = ' '.join([k if isinstance(k, str) else k.name for k in kb.keys])
    shortcut += shortcut.endswith('\\') and '\\' or ''
    if hasattr(kb.filter, 'filters'):
        flt = ' '.join(multi_filter_str(kb.filter))
        multi_filter[(shortcut, flt)] = sentencize(doc)
    else:
        single_filter[(shortcut, name(kb.filter))] = sentencize(doc)


if __name__ == '__main__':
    here = Path(__file__).parent
    dest = here / "source" / "config" / "shortcuts"

    def sort_key(item):
        k, v = item
        shortcut, flt = k
        return (str(shortcut), str(flt))

    for filters, output_filename in [
        (single_filter, "single_filtered"),
        (multi_filter, "multi_filtered"),
    ]:
        with (dest / "{}.csv".format(output_filename)).open("w") as csv:
            for (shortcut, flt), v in sorted(filters.items(), key=sort_key):
                csv.write(":kbd:`{}`\t{}\t{}\n".format(shortcut, flt, v))
