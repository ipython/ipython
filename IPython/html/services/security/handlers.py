#!/usr/bin/env python
# -*- coding: utf-8 -*-

class CSPReportHandler(IPythonHandler):
    '''Accepts a content security policy violation report'''
    @web.authenticated
    @json_errors
    def post(self):
        '''Log a content security policy violation report'''
        csp_report = self.get_json_body()
        self.log.debug(csp_report)

csp_report_uri = r"/api/security/csp-report" 

default_handlers = [
    (csp_report_uri, CSPReportHandler)
]
