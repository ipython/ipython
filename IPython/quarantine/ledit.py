""" Fun magic line editor for ipython

Use this to easily edit lists of strings gradually without crafting long
list comprehensions.

'l' is the magic variable name for every line (array element). Save the current
result (or more exactly, retrieve the last ipython computation result into
%led work area) by running '%led s'. Just run '%led' to show the current work
area data.

Example use:

[ipython]|25> setups = !ls *setup*.py
 ==
['eggsetup.py', 'setup.py', 'setup_bdist_egg.py']
[ipython]|26> setups
         <26> ['eggsetup.py', 'setup.py', 'setup_bdist_egg.py']
[ipython]|27> %led s
Data set from last result (_)
         <27> ['eggsetup.py', 'setup.py', 'setup_bdist_egg.py']
[ipython]|28> %led upper
cmd translated => l.upper()
         <28> ['EGGSETUP.PY', 'SETUP.PY', 'SETUP_BDIST_EGG.PY']
[ipython]|29> %led
Magic line editor (for lists of strings)
current data is:
['eggsetup.py', 'setup.py', 'setup_bdist_egg.py']
[ipython]|30> %led upper
cmd translated => l.upper()
         <30> ['EGGSETUP.PY', 'SETUP.PY', 'SETUP_BDIST_EGG.PY']
[ipython]|31> %led s
Data set from last result (_)
         <31> ['EGGSETUP.PY', 'SETUP.PY', 'SETUP_BDIST_EGG.PY']
[ipython]|32> %led "n:" + l
         <32> ['n:EGGSETUP.PY', 'n:SETUP.PY', 'n:SETUP_BDIST_EGG.PY']
[ipython]|33> %led s
Data set from last result (_)
         <33> ['n:EGGSETUP.PY', 'n:SETUP.PY', 'n:SETUP_BDIST_EGG.PY']
[ipython]|34> %led l.
l.__add__          l.__gt__           l.__reduce_ex__    l.endswith         l.join             l.rstrip
l.__class__        l.__hash__         l.__repr__         l.expandtabs       l.ljust            l.split

... (completions for string variable shown ) ...

"""
from IPython.core import ipapi
import pprint
ip = ipapi.get()

curdata = []

def line_edit_f(self, cmd ):
    global curdata

    if not cmd:

        print "Magic line editor (for lists of strings)"
        if curdata:
            print "current data is:"
            pprint.pprint(curdata)
        else:
            print "No current data, you should set it by running '%led s'"
            print "When you have your data in _ (result of last computation)."
        return

    if cmd == 's':
        curdata = ip.ev('_')
        print "Data set from last result (_)"
        newlines = curdata

    else:
        # simple method call, e.g. upper
        if cmd.isalpha():
            cmd = 'l.' + cmd + '()'
            print "cmd translated =>",cmd

        newlines = []
        for l in curdata:
            try:
                l2 = eval(cmd)
            except Exception,e:
                print "Dropping exception",e,"on line:",l
                continue
            newlines.append(l2)


    return newlines

def line_edit_complete_f(self,event):
    """ Show all string methods in completions """
    if event.symbol.startswith('l.'):
        return ['l.' + func for func in dir('')]

    return dir('') + ['l.' + func for func in dir('')]

ip.set_hook('complete_command', line_edit_complete_f , str_key = '%led')

ip.define_magic('led', line_edit_f)