"""Module containing a preprocessor that removes the outputs from code cells"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import sys

try:
    from queue import Empty  # Py 3
except ImportError:
    from Queue import Empty  # Py 2

from IPython.utils.traitlets import List, Unicode

from IPython.nbformat.current import reads, NotebookNode, writes
from .base import Preprocessor
from IPython.utils.traitlets import Integer

class ExecutePreprocessor(Preprocessor):
    """
    Executes all the cells in a notebook
    """
    
    timeout = Integer(30, config=True,
        help="The time to wait (in seconds) for output from executions."
    )
    # FIXME: to be removed with nbformat v4
    # map msg_type to v3 output_type
    msg_type_map = {
        "error" : "pyerr",
        "execute_result" : "pyout",
    }
    
    # FIXME: to be removed with nbformat v4
    # map mime-type to v3 mime-type keys
    mime_map = {
        "text/plain" : "text",
        "text/html" : "html",
        "image/svg+xml" : "svg",
        "image/png" : "png",
        "image/jpeg" : "jpeg",
        "text/latex" : "latex",
        "application/json" : "json",
        "application/javascript" : "javascript",
    }
    
    extra_arguments = List(Unicode)

    def preprocess(self, nb, resources):
        from IPython.kernel import run_kernel
        kernel_name = nb.metadata.get('kernelspec', {}).get('name', 'python')
        with run_kernel(kernel_name=kernel_name,
                        extra_arguments=self.extra_arguments,
                        stderr=open(os.devnull, 'w')) as kc:
            self.kc = kc
            nb, resources = super(ExecutePreprocessor, self).preprocess(nb, resources)
        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):
        """
        Apply a transformation on each code cell. See base.py for details.
        """
        if cell.cell_type != 'code':
            return cell, resources
        try:
            outputs = self.run_cell(self.kc.shell_channel, self.kc.iopub_channel, cell)
        except Exception as e:
            self.log.error("failed to run cell: " + repr(e))
            self.log.error(str(cell.input))
            raise
        cell.outputs = outputs
        return cell, resources

    def run_cell(self, shell, iopub, cell):
        msg_id = shell.execute(cell.input)
        self.log.debug("Executing cell:\n%s", cell.input)
        # wait for finish, with timeout
        while True:
            try:
                msg = shell.get_msg(timeout=self.timeout)
            except Empty:
                self.log.error("Timeout waiting for execute reply")
                raise
            if msg['parent_header'].get('msg_id') == msg_id:
                break
            else:
                # not our reply
                continue
        
        outs = []

        while True:
            try:
                msg = iopub.get_msg(timeout=self.timeout)
            except Empty:
                self.log.warn("Timeout waiting for IOPub output")
                break
            if msg['parent_header'].get('msg_id') != msg_id:
                # not an output from our execution
                continue

            msg_type = msg['msg_type']
            self.log.debug("output: %s", msg_type)
            content = msg['content']
            out = NotebookNode(output_type=self.msg_type_map.get(msg_type, msg_type))

            # set the prompt number for the input and the output
            if 'execution_count' in content:
                cell['prompt_number'] = content['execution_count']
                out.prompt_number = content['execution_count']

            if msg_type == 'status':
                if content['execution_state'] == 'idle':
                    break
                else:
                    continue
            elif msg_type in {'execute_input', 'pyin'}:
                continue
            elif msg_type == 'clear_output':
                outs = []
                continue

            if msg_type == 'stream':
                out.stream = content['name']
                out.text = content['data']
            elif msg_type in ('display_data', 'execute_result'):
                out['metadata'] = content['metadata']
                for mime, data in content['data'].items():
                    # map mime-type keys to nbformat v3 keys
                    # this will be unnecessary in nbformat v4
                    key = self.mime_map.get(mime, mime)
                    out[key] = data
            elif msg_type == 'error':
                out.ename = content['ename']
                out.evalue = content['evalue']
                out.traceback = content['traceback']
            else:
                self.log.error("unhandled iopub msg: " + msg_type)

            outs.append(out)
        return outs
