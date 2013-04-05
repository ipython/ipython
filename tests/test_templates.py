import io
import nose.tools as nt
import os
from nose.tools import nottest
from converters.template import ConverterTemplate
from  IPython.config.loader import PyFileConfigLoader 
from IPython.config.loader import load_pyconfig_files


@nottest
def cleanfile(stn):
    return filter(None, map(unicode.strip, stn.split('\n')))

@nottest
def compfiles(stra, strb):
    nt.assert_equal(cleanfile(stra),
                    cleanfile(strb))

def test_evens():
    reflist = [
            'tests/ipynbref/IntroNumPy.orig'
            ]

    test_profiles = [prof for prof in os.listdir('profile/test/') if prof.endswith('.py')]

    ### null template should return empty
    for prof in test_profiles :
        yield check_null_profile,prof
    ### end null test

    for ipynb in [
            'IntroNumPy.orig.ipynb',
            '00_notebook_tour.orig.ipynb'
            ]:
        for k,v in {'rst':'.rst','full_html':'.html','latex_base':'.tex'}.iteritems():
            yield test_profile,k,'tests/ipynbref/'+ipynb,'tests/template_ref/'+ipynb[:-6].replace('.','_')+v

@nottest
def check_null_profile(profile):
    loader = PyFileConfigLoader(profile, path=[os.path.join(os.getcwdu(),'profile/test')])
    config = loader.load_config()
    C = ConverterTemplate(config=config)
    result,_ = C.from_filename('tests/ipynbref/IntroNumPy.orig.ipynb')
    nt.assert_equal(result.strip('\n'),'')


@nottest
def test_profile(profile_name,infile, reference_file):
    loader = PyFileConfigLoader(profile_name+'.py',path=[os.path.join(os.getcwdu(),'profile/')])
    config = loader.load_config()
    C = ConverterTemplate(config=config)
    output,resources = C.from_filename(infile)
    with io.open(reference_file,'r') as f:
        compfiles(output,f.read())

