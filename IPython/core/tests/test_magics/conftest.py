import pytest


@pytest.fixture
def ipython():
    '''Get access to the global IPython instance.'''
    return get_ipython()
