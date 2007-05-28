#import IPython.ipapi
#ip = IPython.ipapi.get()

import os

def main():
    root = os.environ.get('IPYKITROOT', None)
    if not root:
        print "Can't configure ipykit, IPYKITROOT should be set."
        return
    
    os.environ["PATH"] = os.environ["PATH"] + ";" + root + "\\bin;"

main()


