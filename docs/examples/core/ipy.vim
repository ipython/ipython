if !exists("$IPY_SESSION")
    finish
endif

" set up the python interpreter within vim, to have all the right modules
" imported, as well as certain useful globals set
python import socket
python import os
python import vim
python from IPython.Debugger import Pdb
python IPYSERVER = None
python reselect = True

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
    print "\'run %s\' sent to ipython" % vim.current.buffer.name

def run_this_line():
    if check_server():
        send(vim.current.line)
        print "line \'%s\' sent to ipython"% vim.current.line
    else:
        raise Exception, "Not connected to an IPython server"

def run_these_lines():
    r = vim.current.range
    if check_server():
        #send(str((vim.current.range.start,vim.current.range.end)))
        for l in vim.current.buffer[r.start:r.end+1]:
            send(str(l)+'\n')
            #send(str(vim.current.buffer[vim.current.range.start:vim.current.range.end]).join("\n"))
        #print "lines %d-%d sent to ipython"% (r.start,r.end)
    else:
        raise Exception, "Not connected to an IPython server"
    
    #reselect the previously highlighted block
    if reselect:
        vim.command("normal gv")
    #vim lines start with 1
    print "lines %d-%d sent to ipython"% (r.start+1,r.end+1)

def toggle_reselect():
    global reselect
    reselect=not reselect
    print "F9 will%sreselect lines after sending to ipython"% (reselect and " " or " not ")

def set_breakpoint():
    if check_server():
        send("__IP.InteractiveTB.pdb.set_break('%s',%d)" % (vim.current.buffer.name,
                                                            vim.current.window.cursor[0]))
        print "set breakpoint in %s:%d"% (vim.current.buffer.name, 
                                          vim.current.window.cursor[0])
    else:
        raise Exception, "Not connected to an IPython server"
    
def clear_breakpoint():
    if check_server():
        send("__IP.InteractiveTB.pdb.clear_break('%s',%d)" % (vim.current.buffer.name,
                                                              vim.current.window.cursor[0]))
        print "clearing breakpoint in %s:%d" % (vim.current.buffer.name,
                                                vim.current.window.cursor[0])
    else:
        raise Exception, "Not connected to an IPython server"

def clear_all_breakpoints():
    if check_server():
        send("__IP.InteractiveTB.pdb.clear_all_breaks()");
        print "clearing all breakpoints"
    else:
        raise Exception, "Not connected to an IPython server"

def run_this_file_pdb():
    if check_server():
        send(' __IP.InteractiveTB.pdb.run(\'execfile("%s")\')' % (vim.current.buffer.name,))
    else:
        raise Exception, "Not connected to an IPython server"
    print "\'run %s\' using pdb sent to ipython" % vim.current.buffer.name

    #XXX: have IPYSERVER print the prompt (look at Leo example)
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
map <silent> <S-F5> :python run_this_line()<CR>
map <silent> <F9> :python run_these_lines()<CR>
map <silent> <S-F9> :python toggle_reselect()<CR>
map <silent> <C-F6> :python send('%pdb')<CR>
map <silent> <F6> :python set_breakpoint()<CR>
map <silent> <s-F6> :python clear_breakpoint()<CR>
map <silent> <F7> :python run_this_file_pdb()<CR>
map <silent> <s-F7> :python clear_all_breaks()<CR>
imap <C-F5> <ESC><F5>a
imap <S-F5> <ESC><S-F5>a
imap <silent> <F5> <ESC><F5>a
map <C-F5> :call <SID>toggle_send_on_save()<CR>
py connect()
