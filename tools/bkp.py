#!/usr/bin/env python
"""Backup directories using rsync. Quick and dirty.

backup.py config_file final_actions
"""

#----------------------------------------------------------------------------
# configure in this section

# all dirs relative to current dir.

# output directory for backups
outdir = ''

# list directories to backup as a dict with 1 or 0 values for
# recursive (or not) descent:
to_backup = {}

# list exclude patterns here (space-separated):
# if the pattern ends with a / then it will only match a directory, not a
# file, link or device.
# see man rsync for more details on the exclude patterns
exc_pats = '#*#  *~  *.pyc *.pyo *.o '

# global options for rsync
rsync_opts='-v -t -a --delete --delete-excluded'

#----------------------------------------------------------------------------
# real code begins
import os,string,re,sys
from IPython.genutils import *
from IPython.Itpl import itpl

# config file can redefine final actions
def final():
    pass

# load config from cmd line config file or default bkprc.py
try:
    execfile(sys.argv[1])
except:
    try:
        execfile('bkprc.py')
    except IOError:
        print 'You need to provide a config file: bkp.py rcfile'
        sys.exit()

# make output dir if needed
outdir = os.path.expanduser(outdir)
try:
    os.makedirs(outdir)
except OSError:  # raised if dir already exists -> no need to make it
    pass

# build rsync command and call:
exclude = re.sub(r'([^\s].*?)(\s|$)',r'--exclude "\1"\2',exc_pats)
rsync = itpl('rsync $rsync_opts $exclude')

# the same can also be done with lists (keep it for reference):
#exclude = string.join(['--exclude "'+p+'"' for p in qw(exc_pats)])

# rsync takes -r as a flag, not 0/1 so translate:
rec_flag = {0:'',1:'-r'}

# loop over user specified directories calling rsync
for bakdir,rec in to_backup.items():
    bakdir = os.path.expanduser(bakdir)
    xsys(itpl('$rsync $rec_flag[rec] $bakdir $outdir'),
         debug=0,verbose=1,header='\n### ')

# final actions?
final()
