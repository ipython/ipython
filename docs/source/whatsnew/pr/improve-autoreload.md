magic `%autoreload 2` now captures new methods added to classes. Earlier, only methods existing as of the initial import were being tracked and updated.  

This new feature helps dual environement development - Jupyter+IDE - where the code gradually moves from notebook cells to package files, as it gets structured.

**Example**: An instance of the class `MyClass` will be able to access the method `cube()` after it is uncommented and the file `file1.py` saved on disk.

````python
# notebook

from mymodule import MyClass
first = MyClass(5)
````

````python
# mymodule/file1.py

class MyClass:

    def __init__(self, a=10):
        self.a = a

    def square(self):
        print('compute square')
        return self.a*self.a

    # def cube(self):
    #     print('compute cube')
    #     return self.a*self.a*self.a
````

