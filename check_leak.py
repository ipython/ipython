import sqlite3
import time
import threading
import gc
import os
from IPython.core.history import HistoryManager
from IPython.core.interactiveshell import InteractiveShell

def test_leak():
    shell = InteractiveShell()

    # Mock connect to be slow
    orig_connect = sqlite3.connect
    def slow_connect(*args, **kwargs):
        if threading.current_thread().name == "IPythonHistorySavingThread":
            # print("Thread connecting...")
            time.sleep(2)
        return orig_connect(*args, **kwargs)
    sqlite3.connect = slow_connect

    HistoryManager._max_inst = 10
    HistoryManager._instances.clear()

    print("Creating HM1")
    hm1 = HistoryManager(shell=shell, hist_file='test_leak.sqlite')
    st = hm1.save_thread

    # Wait a bit for the thread to reach connect()
    time.sleep(0.5)

    # At this point, the thread is likely still in sqlite3.connect because of slow_connect
    print(f"Instances after creating HM1: {len(HistoryManager._instances)}")

    # Drop reference
    del hm1
    gc.collect()

    print(f"Instances after dropping HM1 reference: {len(HistoryManager._instances)}")

    if len(HistoryManager._instances) > 0:
        print("HM1 is still alive because the background thread holds a strong reference.")

    # Cleanup
    if st:
        st.stop()
    sqlite3.connect = orig_connect
    gc.collect()
    print(f"Instances after stopping thread: {len(HistoryManager._instances)}")

    if os.path.exists('test_leak.sqlite'):
        os.remove('test_leak.sqlite')

if __name__ == "__main__":
    test_leak()
