#!/usr/bin/env python
# encoding: utf-8
"""
Job and task components for writing .xml files that the Windows HPC Server 
2008 can use to start jobs.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import with_statement

import os
import re

from xml.etree import ElementTree as ET
from xml.dom import minidom

from IPython.core.component import Component
from IPython.external import Itpl
from IPython.utils.traitlets import (
    Str, Int, List, Unicode, Instance,
    Enum, Bool
)

#-----------------------------------------------------------------------------
# Job and Task Component
#-----------------------------------------------------------------------------


def as_str(value):
    if isinstance(value, str):
        return value
    elif isinstance(value, bool):
        if value:
            return 'true'
        else:
            return 'false'
    elif isinstance(value, (int, float)):
        return repr(value)
    else:
        return value


def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


class WinHPCJob(Component):

    job_id = Str('')
    job_name = Str('MyJob', config=True)
    min_cores = Int(1, config=True)
    max_cores = Int(1, config=True)
    min_sockets = Int(1, config=True)
    max_sockets = Int(1, config=True)
    min_nodes = Int(1, config=True)
    max_nodes = Int(1, config=True)
    unit_type = Str("Core", config=True)
    auto_calculate_min = Bool(True, config=True)
    auto_calculate_max = Bool(True, config=True)
    run_until_canceled = Bool(False, config=True)
    is_exclusive = Bool(False, config=True)
    username = Str(os.environ.get('USERNAME', ''), config=True)
    owner = Str('', config=True)
    job_type = Str('Batch', config=True)
    priority = Enum(('Lowest','BelowNormal','Normal','AboveNormal','Highest'),
        default_value='Highest', config=True)
    requested_nodes = Str('', config=True)
    project = Str('IPython', config=True)
    xmlns = Str('http://schemas.microsoft.com/HPCS2008/scheduler/')
    version = Str("2.000")
    tasks = List([])

    def _username_changed(self, name, old, new):
        self.owner = new

    def _write_attr(self, root, attr, key):
        s = as_str(getattr(self, attr, ''))
        if s:
            root.set(key, s)

    def as_element(self):
        # We have to add _A_ type things to get the right order than
        # the MSFT XML parser expects.
        root = ET.Element('Job')
        self._write_attr(root, 'version', '_A_Version')
        self._write_attr(root, 'job_name', '_B_Name')
        self._write_attr(root, 'unit_type', '_C_UnitType')
        self._write_attr(root, 'min_cores', '_D_MinCores')
        self._write_attr(root, 'max_cores', '_E_MaxCores')
        self._write_attr(root, 'min_sockets', '_F_MinSockets')
        self._write_attr(root, 'max_sockets', '_G_MaxSockets')
        self._write_attr(root, 'min_nodes', '_H_MinNodes')
        self._write_attr(root, 'max_nodes', '_I_MaxNodes')
        self._write_attr(root, 'run_until_canceled', '_J_RunUntilCanceled')
        self._write_attr(root, 'is_exclusive', '_K_IsExclusive')
        self._write_attr(root, 'username', '_L_UserName')
        self._write_attr(root, 'job_type', '_M_JobType')
        self._write_attr(root, 'priority', '_N_Priority')
        self._write_attr(root, 'requested_nodes', '_O_RequestedNodes')
        self._write_attr(root, 'auto_calculate_max', '_P_AutoCalculateMax')
        self._write_attr(root, 'auto_calculate_min', '_Q_AutoCalculateMin')
        self._write_attr(root, 'project', '_R_Project')
        self._write_attr(root, 'owner', '_S_Owner')
        self._write_attr(root, 'xmlns', '_T_xmlns')
        dependencies = ET.SubElement(root, "Dependencies")
        etasks = ET.SubElement(root, "Tasks")
        for t in self.tasks:
            etasks.append(t.as_element())
        return root

    def tostring(self):
        """Return the string representation of the job description XML."""
        root = self.as_element()
        indent(root)
        txt = ET.tostring(root, encoding="utf-8")
        # Now remove the tokens used to order the attributes.
        txt = re.sub(r'_[A-Z]_','',txt)
        txt = '<?xml version="1.0" encoding="utf-8"?>\n' + txt
        return txt

    def write(self, filename):
        """Write the XML job description to a file."""
        txt = self.tostring()
        with open(filename, 'w') as f:
            f.write(txt)

    def add_task(self, task):
        """Add a task to the job.

        Parameters
        ----------
        task : :class:`WinHPCTask`
            The task object to add.
        """
        self.tasks.append(task)


class WinHPCTask(Component):

    task_id = Str('')
    task_name = Str('')
    version = Str("2.000")
    min_cores = Int(1, config=True)
    max_cores = Int(1, config=True)
    min_sockets = Int(1, config=True)
    max_sockets = Int(1, config=True)
    min_nodes = Int(1, config=True)
    max_nodes = Int(1, config=True)
    unit_type = Str("Core", config=True)
    command_line = Str('', config=True)
    work_directory = Str('', config=True)
    is_rerunnaable = Bool(True, config=True)
    std_out_file_path = Str('', config=True)
    std_err_file_path = Str('', config=True)
    is_parametric = Bool(False, config=True)
    environment_variables = Instance(dict, args=())

    def _write_attr(self, root, attr, key):
        s = as_str(getattr(self, attr, ''))
        if s:
            root.set(key, s)

    def as_element(self):
        root = ET.Element('Task')
        self._write_attr(root, 'version', '_A_Version')
        self._write_attr(root, 'task_name', '_B_Name')
        self._write_attr(root, 'min_cores', '_C_MinCores')
        self._write_attr(root, 'max_cores', '_D_MaxCores')
        self._write_attr(root, 'min_sockets', '_E_MinSockets')
        self._write_attr(root, 'max_sockets', '_F_MaxSockets')
        self._write_attr(root, 'min_nodes', '_G_MinNodes')
        self._write_attr(root, 'max_nodes', '_H_MaxNodes')
        self._write_attr(root, 'command_line', '_I_CommandLine')
        self._write_attr(root, 'work_directory', '_J_WorkDirectory')
        self._write_attr(root, 'is_rerunnaable', '_K_IsRerunnable')
        self._write_attr(root, 'std_out_file_path', '_L_StdOutFilePath')
        self._write_attr(root, 'std_err_file_path', '_M_StdErrFilePath')
        self._write_attr(root, 'is_parametric', '_N_IsParametric')
        self._write_attr(root, 'unit_type', '_O_UnitType')
        root.append(self.get_env_vars())
        return root

    def get_env_vars(self):
        env_vars = ET.Element('EnvironmentVariables')
        for k, v in self.environment_variables.items():
            variable = ET.SubElement(env_vars, "Variable")
            name = ET.SubElement(variable, "Name")
            name.text = k
            value = ET.SubElement(variable, "Value")
            value.text = v
        return env_vars


# j = WinHPCJob(None)
# j.job_name = 'IPCluster'
# j.username = 'GNET\\bgranger'
# j.requested_nodes = 'GREEN'
# 
# t = WinHPCTask(None)
# t.task_name = 'Controller'
# t.command_line = r"\\blue\domainusers$\bgranger\Python\Python25\Scripts\ipcontroller.exe --log-to-file -p default --log-level 10"
# t.work_directory = r"\\blue\domainusers$\bgranger\.ipython\cluster_default"
# t.std_out_file_path = 'controller-out.txt'
# t.std_err_file_path = 'controller-err.txt'
# t.environment_variables['PYTHONPATH'] = r"\\blue\domainusers$\bgranger\Python\Python25\Lib\site-packages"
# j.add_task(t)

