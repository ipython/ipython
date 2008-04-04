import os
def oscmd(c):
        os.system(c)
oscmd('sphinx-build -d build/doctrees source build/html')