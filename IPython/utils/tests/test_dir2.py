from IPython.utils.dir2 import dir2


class Base(object):
    x = 1
    z = 23


def test_base():
    res = dir2(Base())
    assert res[-2:] == ['x', 'z']
    assert 'y' not in res
    assert '__class__' in res
    assert res.count('x') == 1, res.count('x')


def test_SubClass():

    class SubClass(Base):
        y = 2

    res = dir2(SubClass())
    assert res[-3:] == ['x', 'y', 'z']
    assert res.count('x') == 1 , res.count('x')


def test_SubClass_with_trait_names_method():

    class SubClass(Base):
        y = 2
        def trait_names(self):
            return ['t', 'umbrella']

    res = dir2(SubClass())
    assert res[-6:] == ['t', 'trait_names', 'umbrella', 'x', 'y', 'z'], res
    assert res.count('x') == 1, res.count('x')


def test_SubClass_with_trait_names_attr():
    # usecase: trait_names is used in a class describing psychological classification

    class SubClass(Base):
        y = 2
        trait_names = 44

    res = dir2(SubClass())
    assert res[-4:] == ['trait_names', 'x', 'y', 'z'], res



def test_all_basic_ok():

    class ALL(Base):
        __all__ = ['x']

    assert dir2(ALL()) == ['x']


def test_all_dynamic_ok():

    class ALL(object):
        __all__ = ['special']
        def __getattr__(self, attr):
            if attr == 'special':
                return attr
            raise AttributeError

    assert dir2(ALL()) == ['special']


def test_all_allows_anything():
    # this is to permit the general dynamic case above. If we force the result to be in dir(), we will
    # restrict the __all__ case to that which then differs from the import use of __all__. Yes I know that
    # it could be rubbish, but python is a "language for consenting adults" - and it won't cause ipython to crash
    # in this worst case; the user will get an attribute error when accessing the attribute, as he/she would when
    # accessing it in code

    class ALL(object):
        __all__ = ['anything']

    assert dir2(ALL()) == ['anything']


def test_all_non_string_entries_ok():

    class ALL(Base):
        __all__ = [1.5, Base(), 'x']

    assert dir2(ALL()) == ['x']


def test_all_tuple_ok():

    class ALL(Base):
        __all__ = ('x',)


    assert dir2(ALL()) == ['x']

def test_all_set_ok():

    class ALL(Base):
        __all__ = set('x')

    assert dir2(ALL()) == ['x']


def test_all_dict_ignores_all_ok():

    class ALL(object):
        x = 4
        y = 5
        __all__ = {'x': x}

    res = dir2(ALL())
    assert res[-2:] == ['x', 'y'], res
