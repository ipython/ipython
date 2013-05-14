import re

def remove_ansi(src):
    return re.sub(r'\033\[(0|\d;\d\d)m', '', src)


def ansi2html(txt):
    ansi_colormap = {
        '30': 'ansiblack',
        '31': 'ansired',
        '32': 'ansigreen',
        '33': 'ansiyellow',
        '34': 'ansiblue',
        '35': 'ansipurple',
        '36': 'ansicyan',
        '37': 'ansigrey',
        '01': 'ansibold',
    }

    # do ampersand first
    txt = txt.replace('&', '&amp;')
    html_escapes = {
        '<': '&lt;',
        '>': '&gt;',
        "'": '&apos;',
        '"': '&quot;',
        '`': '&#96;',
    }
    
    for c, escape in html_escapes.iteritems():
        txt = txt.replace(c, escape)

    ansi_re = re.compile('\x1b' + r'\[([\dA-Fa-f;]*?)m')
    m = ansi_re.search(txt)
    opened = False
    cmds = []
    opener = ''
    closer = ''
    while m:
        cmds = m.groups()[0].split(';')
        closer = '</span>' if opened else ''
        
        # True if there is there more than one element in cmds, *or*
        # if there is only one but it is not equal to a string of zeroes.
        opened = len(cmds) > 1 or cmds[0] != '0' * len(cmds[0])
        classes = []
        for cmd in cmds:
            if cmd in ansi_colormap:
                classes.append(ansi_colormap.get(cmd))

        if classes:
            opener = '<span class="%s">' % (' '.join(classes))
        else:
            opener = ''
        txt = re.sub(ansi_re, closer + opener, txt, 1)

        m = ansi_re.search(txt)

    if opened:
        txt += '</span>'
    return txt