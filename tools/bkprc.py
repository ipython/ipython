# config file for a quick'n dirty backup script that uses rsync

# output directory for backups
outdir = '~/tmp'

# list directories to backup as a dict with 1 or 0 values for
# recursive (or not) descent:
to_backup = {'~/ipython/ipython':1}

# exclude patterns. anything ending in / is considered a directory
exc_pats = '#*#  *~ *.o *.pyc *.pyo MANIFEST *.pdf *.flc build/ dist/ ' \
' doc/manual/ doc/manual.lyx ChangeLog.* magic.tex *.1.gz '

# final actions after doing the backup
def final():
    dbg = 0
    version = bq('ipython -V')
    out_tgz = outdir+'/ipython-'+version+'.tgz'
    xsys(itpl('cd $outdir; pwd;tar -czf $out_tgz ipython'),debug=dbg,verbose=1)
    #xsys(itpl('cp $out_tgz /mnt/card/fperez/ipython'),debug=dbg,verbose=1)
    xsys(itpl('mv $out_tgz ~/ipython/backup'),debug=dbg,verbose=1)
    xsys(itpl('rm -rf ${outdir}/ipython'),debug=dbg,verbose=1)
