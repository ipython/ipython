"""
A Distributed Hello world
Ken Kinder <ken@kenkinder.com>
"""
from IPython.kernel import client

tc = client.TaskClient()
mec = client.MultiEngineClient()

mec.execute('import time')
hello_taskid = tc.run(client.StringTask('time.sleep(3) ; word = "Hello,"', pull=('word')))
world_taskid = tc.run(client.StringTask('time.sleep(3) ; word = "World!"', pull=('word')))
print "Submitted tasks:", hello_taskid, world_taskid
print tc.get_task_result(hello_taskid,block=True).ns.word, tc.get_task_result(world_taskid,block=True).ns.word
