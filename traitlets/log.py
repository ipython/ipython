"""Grab the global logger instance."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import logging

_logger = None

def get_logger():
    """Grab the global logger instance.
    
    If a global IPython Application is instantiated, grab its logger.
    Otherwise, grab the root logger.
    """
    global _logger
    
    if _logger is None:
        from IPython.config import Application
        if Application.initialized():
            _logger = Application.instance().log
        else:
            logging.basicConfig()
            _logger = logging.getLogger()
    return _logger
