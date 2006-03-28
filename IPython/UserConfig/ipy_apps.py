import IPython.ipapi
ip = IPython.ipapi.get()

def main():
    ip.magic('rehashdir c:/opt/kdiff3')

main()
