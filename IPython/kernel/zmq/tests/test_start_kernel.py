import nose.tools as nt

from .test_embed_kernel import setup, teardown, setup_kernel

TIMEOUT = 15

def test_ipython_start_kernel_userns():
    cmd = ('from IPython import start_kernel\n'
           'ns = {"tre": 123}\n'
           'start_kernel(user_ns=ns)')
    
    with setup_kernel(cmd) as client:
        msg_id = client.object_info('tre')
        msg = client.get_shell_msg(block=True, timeout=TIMEOUT)
        content = msg['content']
        assert content['found']
        nt.assert_equal(content['string_form'], u'123')