"""Module containing a preprocessor that removes the outputs from code cells"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os

try:
    from queue import Empty  # Py 3
except ImportError:
    from Queue import Empty  # Py 2

from IPython.utils.traitlets import List, Unicode

from IPython.nbformat.v4 import output_from_msg
from .base import Preprocessor
from IPython.utils.traitlets import Integer


class ExecutePreprocessor(Preprocessor):
    """
    Executes all the cells in a notebook
    """
    
    timeout = Integer(30, config=True,
        help="The time to wait (in seconds) for output from executions."
    )
    
    extra_arguments = List(Unicode)

    def preprocess(self, nb, resources):
        from IPython.kernel import run_kernel
        kernel_name = nb.metadata.get('kernelspec', {}).get('name', 'python')
        self.log.info("Executing notebook with kernel: %s" % kernel_name)
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
            outputs = self.run_cell(cell)
        except Exception as e:
            self.log.error("failed to run cell: " + repr(e))
            self.log.error(str(cell.source))
            raise
        cell.outputs = outputs
        return cell, resources

    def run_cell(self, cell):
        msg_id = self.kc.execute(cell.source)
        self.log.debug("Executing cell:\n%s", cell.source)
        # wait for finish, with timeout
        while True:
            try:
                msg = self.kc.shell_channel.get_msg(timeout=self.timeout)
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
                msg = self.kc.iopub_channel.get_msg(timeout=self.timeout)
            except Empty:
                self.log.warn("Timeout waiting for IOPub output")
                break
            if msg['parent_header'].get('msg_id') != msg_id:
                # not an output from our execution
                continue

            msg_type = msg['msg_type']
            self.log.debug("output: %s", msg_type)
            content = msg['content']

            # set the prompt number for the input and the output
            if 'execution_count' in content:
                cell['execution_count'] = content['execution_count']

            if msg_type == 'status':
                if content['execution_state'] == 'idle':
                    break
                else:
                    continue
            elif msg_type == 'execute_input':
                continue
            elif msg_type == 'clear_output':
                outs = []
                continue

            try:
                out = output_from_msg(msg)
            except ValueError:
                self.log.error("unhandled iopub msg: " + msg_type)
            else:
                outs.append(out)

        return outs
