"""Module containing a preprocessor that removes the outputs from code cells"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import sys

from Queue import Empty
from IPython.kernel import KernelManager
from IPython.nbformat.current import reads, NotebookNode, writes

from .base import Preprocessor


#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class ExecutePreprocessor(Preprocessor):
    """
    Executes all the cells in a notebook
    """
    def __init__(self, *args, **kwargs):
        """
        Start an kernel to run the Python code
        """
        super(ExecutePreprocessor, self).__init__(*args, **kwargs)
        self.km = KernelManager()
        # run %pylab inline, because some notebooks assume this
        # even though they shouldn't
        self.km.start_kernel(extra_arguments=['--pylab=inline'], stderr=open(os.devnull, 'w'))
        self.kc = self.km.client()
        self.kc.start_channels()
        self.iopub = self.kc.iopub_channel
        self.shell = self.kc.shell_channel
        
        self.shell.execute("pass")
        self.shell.get_msg()
                    
    def preprocess_cell(self, cell, resources, cell_index):
        """
        Apply a transformation on each code cell. See base.py for details.
        """
        if cell.cell_type != 'code':
            return cell, resources
        try:
            outputs = self.run_cell(self.shell, self.iopub, cell)
        except Exception as e:
            print >> sys.stderr, "failed to run cell:", repr(e)
            print >> sys.stderr, cell.input
            sys.exit(1)
        cell.outputs = outputs
        return cell, resources

    @staticmethod
    def run_cell(shell, iopub, cell):
        # print cell.input
        shell.execute(cell.input)
        # wait for finish, maximum 20s
        shell.get_msg(timeout=20)
        outs = []
        
        while True:
            try:
                msg = iopub.get_msg(timeout=0.2)
            except Empty:
                break
            msg_type = msg['msg_type']
            if msg_type in ('status', 'pyin'):
                continue
            elif msg_type == 'clear_output':
                outs = []
                continue
            
            content = msg['content']
            # print msg_type, content
            out = NotebookNode(output_type=msg_type)
            
            if msg_type == 'stream':
                out.stream = content['name']
                out.text = content['data']
            elif msg_type in ('display_data', 'pyout'):
                out['metadata'] = content['metadata']
                for mime, data in content['data'].iteritems():
                    attr = mime.split('/')[-1].lower()
                    # this gets most right, but fix svg+html, plain
                    attr = attr.replace('+xml', '').replace('plain', 'text')
                    setattr(out, attr, data)
                if msg_type == 'pyout':
                    out.prompt_number = content['execution_count']
            elif msg_type == 'pyerr':
                out.ename = content['ename']
                out.evalue = content['evalue']
                out.traceback = content['traceback']
            else:
                print >> sys.stderr, "unhandled iopub msg:", msg_type
            
            outs.append(out)
        return outs
        

    def __del__(self):
        self.kc.stop_channels()
        self.km.shutdown_kernel()
        del self.km
