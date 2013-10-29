# encoding: utf-8
"""
Job and task components for writing .xml files that the Windows HPC Server
2008 can use to start jobs.

Authors:

* Brian Granger
* MinRK

"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import re
import uuid

from xml.etree import ElementTree as ET

from IPython.config.configurable import Configurable
from IPython.utils.py3compat import iteritems
from IPython.utils.traitlets import (
    Unicode, Integer, List, Instance,
    Enum, Bool
)

#-----------------------------------------------------------------------------
# Job and Task classes
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


def find_username():
    domain = os.environ.get('USERDOMAIN')
    username = os.environ.get('USERNAME','')
    if domain is None:
        return username
    else:
        return '%s\\%s' % (domain, username)


class WinHPCJob(Configurable):

    job_id = Unicode('')
    job_name = Unicode('MyJob', config=True)
    min_cores = Integer(1, config=True)
    max_cores = Integer(1, config=True)
    min_sockets = Integer(1, config=True)
    max_sockets = Integer(1, config=True)
    min_nodes = Integer(1, config=True)
    max_nodes = Integer(1, config=True)
    unit_type = Unicode("Core", config=True)
    auto_calculate_min = Bool(True, config=True)
    auto_calculate_max = Bool(True, config=True)
    run_until_canceled = Bool(False, config=True)
    is_exclusive = Bool(False, config=True)
    username = Unicode(find_username(), config=True)
    job_type = Unicode('Batch', config=True)
    priority = Enum(('Lowest','BelowNormal','Normal','AboveNormal','Highest'),
        default_value='Highest', config=True)
    requested_nodes = Unicode('', config=True)
    project = Unicode('IPython', config=True)
    xmlns = Unicode('http://schemas.microsoft.com/HPCS2008/scheduler/')
    version = Unicode("2.000")
    tasks = List([])

    @property
    def owner(self):
        return self.username

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
        txt = ET.tostring(root, encoding="utf-8").decode('utf-8')
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


class WinHPCTask(Configurable):

    task_id = Unicode('')
    task_name = Unicode('')
    version = Unicode("2.000")
    min_cores = Integer(1, config=True)
    max_cores = Integer(1, config=True)
    min_sockets = Integer(1, config=True)
    max_sockets = Integer(1, config=True)
    min_nodes = Integer(1, config=True)
    max_nodes = Integer(1, config=True)
    unit_type = Unicode("Core", config=True)
    command_line = Unicode('', config=True)
    work_directory = Unicode('', config=True)
    is_rerunnaable = Bool(True, config=True)
    std_out_file_path = Unicode('', config=True)
    std_err_file_path = Unicode('', config=True)
    is_parametric = Bool(False, config=True)
    environment_variables = Instance(dict, args=(), config=True)

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
        for k, v in iteritems(self.environment_variables):
            variable = ET.SubElement(env_vars, "Variable")
            name = ET.SubElement(variable, "Name")
            name.text = k
            value = ET.SubElement(variable, "Value")
            value.text = v
        return env_vars



# By declaring these, we can configure the controller and engine separately!

class IPControllerJob(WinHPCJob):
    job_name = Unicode('IPController', config=False)
    is_exclusive = Bool(False, config=True)
    username = Unicode(find_username(), config=True)
    priority = Enum(('Lowest','BelowNormal','Normal','AboveNormal','Highest'),
        default_value='Highest', config=True)
    requested_nodes = Unicode('', config=True)
    project = Unicode('IPython', config=True)


class IPEngineSetJob(WinHPCJob):
    job_name = Unicode('IPEngineSet', config=False)
    is_exclusive = Bool(False, config=True)
    username = Unicode(find_username(), config=True)
    priority = Enum(('Lowest','BelowNormal','Normal','AboveNormal','Highest'),
        default_value='Highest', config=True)
    requested_nodes = Unicode('', config=True)
    project = Unicode('IPython', config=True)


class IPControllerTask(WinHPCTask):

    task_name = Unicode('IPController', config=True)
    controller_cmd = List(['ipcontroller.exe'], config=True)
    controller_args = List(['--log-to-file', '--log-level=40'], config=True)
    # I don't want these to be configurable
    std_out_file_path = Unicode('', config=False)
    std_err_file_path = Unicode('', config=False)
    min_cores = Integer(1, config=False)
    max_cores = Integer(1, config=False)
    min_sockets = Integer(1, config=False)
    max_sockets = Integer(1, config=False)
    min_nodes = Integer(1, config=False)
    max_nodes = Integer(1, config=False)
    unit_type = Unicode("Core", config=False)
    work_directory = Unicode('', config=False)

    def __init__(self, **kwargs):
        super(IPControllerTask, self).__init__(**kwargs)
        the_uuid = uuid.uuid1()
        self.std_out_file_path = os.path.join('log','ipcontroller-%s.out' % the_uuid)
        self.std_err_file_path = os.path.join('log','ipcontroller-%s.err' % the_uuid)

    @property
    def command_line(self):
        return ' '.join(self.controller_cmd + self.controller_args)


class IPEngineTask(WinHPCTask):

    task_name = Unicode('IPEngine', config=True)
    engine_cmd = List(['ipengine.exe'], config=True)
    engine_args = List(['--log-to-file', '--log-level=40'], config=True)
    # I don't want these to be configurable
    std_out_file_path = Unicode('', config=False)
    std_err_file_path = Unicode('', config=False)
    min_cores = Integer(1, config=False)
    max_cores = Integer(1, config=False)
    min_sockets = Integer(1, config=False)
    max_sockets = Integer(1, config=False)
    min_nodes = Integer(1, config=False)
    max_nodes = Integer(1, config=False)
    unit_type = Unicode("Core", config=False)
    work_directory = Unicode('', config=False)

    def __init__(self, **kwargs):
        super(IPEngineTask,self).__init__(**kwargs)
        the_uuid = uuid.uuid1()
        self.std_out_file_path = os.path.join('log','ipengine-%s.out' % the_uuid)
        self.std_err_file_path = os.path.join('log','ipengine-%s.err' % the_uuid)

    @property
    def command_line(self):
        return ' '.join(self.engine_cmd + self.engine_args)


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

