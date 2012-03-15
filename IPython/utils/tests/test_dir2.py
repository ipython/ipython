from IPython.utils.dir2 import dir2

    
class Base(object): 
    x = 1 
    z = 23  
   
    
class ALL(Base):
    __all__ = ['x']  


class SubClass(Base):
    y = 2
    
class SubClass_with_trait_names(Base):
    y = 2 
    def trait_names(self):
        return 't'
       

def test_base():
    res = dir2(Base()) 
    assert res[-2:] == ['x', 'z']
    assert 'y' not in res
    assert '__class__' in res
    assert res.count('x') == 1, res.count('x') 
    

def test_SubClass():
    res = dir2(SubClass()) 
    assert res[-3:] == ['x', 'y', 'z']
    assert res.count('x') == 1 ,res.count('x')     
 
    
def test_SubClass_with_trait_names():
    res = dir2(SubClass_with_trait_names()) 
    assert res[-5:] == ['t', 'trait_names', 'x', 'y', 'z'], res
    assert res.count('x') == 1, res.count('x')     


def test_all_():
    assert dir2(ALL()) == ['x']         