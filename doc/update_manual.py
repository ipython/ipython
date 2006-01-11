""" Must be launched via ipython not normal python 

in ipython prompt do

> %run update_manual.py
"""

import sys,IPython,re


fil=open("magic.tex","w")
oldout=sys.stdout
sys.stdout=fil
ipmagic("magic -latex")
sys.stdout=oldout
fil.close()

fil=open("manual_base.lyx")
txt=fil.read()
fil.close()

manualtext=re.sub("__version__",IPython.__version__,txt)
fil=open("manual.lyx","w")
fil.write(manualtext)
fil.close()
print "Manual (magic.tex, manual.lyx) succesfully updated!"
