import copy

from IPython.nbformat.current import validate
from .. import convert

from . import nbexamples
from IPython.nbformat.v3.tests import nbexamples as v3examples

def test_upgrade_notebook():
    nb03 = copy.deepcopy(v3examples.nb0)
    validate(nb03)
    nb04 = convert.upgrade(nb03)
    validate(nb04)

def test_downgrade_notebook():
    nb04 = copy.deepcopy(nbexamples.nb0)
    validate(nb04)
    nb03 = convert.downgrade(nb04)
    validate(nb03)
