"""Toy example of reading an SConf object."""

from IPython.external.configobj import ConfigObj
from IPython.external import configobj, validate


from IPython.config import sconfig
reload(sconfig)

configspecfilename = 'simple.spec.conf'
filename = 'simple.conf'

print '*'*80
configspec = ConfigObj(configspecfilename, encoding='UTF8',
                       list_values=False)
print sconfig.configobj2str(configspec)

print '*'*80
config = ConfigObj(filename, configspec=configspec,
                   interpolation='Template',
                   unrepr=True)
print sconfig.configobj2str(config)
vdt = validate.Validator()
test = config.validate(vdt,preserve_errors=True)

####
vdt = validate.Validator()
class Bunch: pass
vf = Bunch()
vf.__dict__.update(vdt.functions)
vf.pass_ = vdt.functions['pass']
vf.__dict__.pop('',None)
vf.__dict__.pop('pass',None)
###


if test==True:
    print 'All OK'
else:
    err = configobj.flatten_errors(config,test)
    print 'Flat errors:'
    for secs,key,result in err:
        if secs == []:
            print 'DEFAULT:','key:',key,'err:',result
        else:
            print 'Secs:',secs,'key:',key,'err:',result


##
print '*'*80

sc = sconfig.SConfig(configspecfilename)



####

            
        
