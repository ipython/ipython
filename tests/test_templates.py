import io
import nose.tools as nt
import os
from nose.tools import nottest
from converters.template import ConverterTemplate
from  IPython.config.loader import PyFileConfigLoader 




def test_evens():
    reflist = [
            'tests/ipynbref/IntroNumPy.orig'
            ]

    test_profiles = [prof for prof in os.listdir('profile/test/') if prof.endswith('.py')]

    ### null template should return empty
    for prof in test_profiles :
        yield check_null_profile,prof
    ### end null test

def check_null_profile(profile):
    loader = PyFileConfigLoader(profile, path=[os.path.join(os.getcwdu(),'profile/test')])
    config = loader.load_config()
    C = ConverterTemplate(config=config)
    result,_ = C.from_filename('tests/ipynbref/IntroNumPy.orig.ipynb')
    nt.assert_equal(result,'')

