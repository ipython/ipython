if !exists("$IPY_SESSION")
    finish
endif

" set up the python interpreter within vim, to have all the right modules
" imported, as well as certain useful globals set
python import socket
python import os
python import vim
python IPYSERVER = None

python << EOF
# do we have a connection to the ipython instance?
def check_server():
    global IPYSERVER
    if IPYSERVER:
        return True
    else:
        return False

# connect to the ipython server, if we need to
def connect():
    global IPYSERVER
    if check_server():
        return
    try:
        IPYSERVER = socket.socket(socket.AF_UNIX)
        IPYSERVER.connect(os.environ.get('IPY_SERVER'))
    except:
        IPYSERVER = None

def disconnect():
    if IPYSERVER:
        IPYSERVER.close()

def send(cmd):
    x = 0
    while True:
        x += IPYSERVER.send(cmd)
        if x < len(cmd):
            cmd = cmd[x:]
        else:
            break

def run_this_file():
    if check_server():
        send('run %s' % (vim.current.buffer.name,))
    else:
        raise Exception, "Not connected to an IPython server"
EOF

fun! <SID>toggle_send_on_save()
    if exists("s:ssos") && s:ssos == 1
        let s:ssos = 0
        au! BufWritePost *.py :py run_this_file()
        echo "Autosend Off"
    else
        let s:ssos = 1
        au BufWritePost *.py :py run_this_file()
        echo "Autowsend On"
    endif
endfun

map <silent> <F5> :python run_this_file()<CR>
imap <silent> <C-F5> <ESC><F5>a
map <F7> :call <SID>toggle_send_on_save()<CR>
py connect()
