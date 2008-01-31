""" Run ipython unit tests

This should be launched from inside ipython by "%run runtests.py"
or through ipython command line "ipython runtests.py".

"""

from IPython.external.path import path
import pprint,os
import IPython.ipapi
ip = IPython.ipapi.get()

def main():
    all = path('.').files('test_*py')
    results = {}
    res_exc = [None]
    def exchook(self,*e):
        res_exc[0] = [e]
    ip.IP.set_custom_exc((Exception,), exchook)
    startdir = os.getcwd()
    for test in all:
        print test
        res_exc[0] = 'ok'
        os.chdir(startdir)
        ip.runlines(test.text())
        results[str(test)] = res_exc[0]
        
    os.chdir(startdir)
    pprint.pprint(results)
        
main()
